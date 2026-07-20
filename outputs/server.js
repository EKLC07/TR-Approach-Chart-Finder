const http = require("http");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { Writable } = require("stream");

const PORT = Number(process.env.PORT || 8787);
const ROOT = __dirname;
const WORK_DIR = path.resolve(ROOT, "..", "work");
const DHMI_BASE = "https://www.dhmi.gov.tr/AIPDocuments";
const CACHE_TTL_MS = 1000 * 60 * 60 * 6;
const PDF_SCAN_LIMIT = 80;
const PYTHON_EXE = "C:\\Users\\Enes\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";

const chartCache = new Map();
const textCache = new Map();
const runwayTagCache = new Map();
let runwayCache = null;

process.on("uncaughtException", (error) => {
  console.error("uncaughtException:", error);
});

process.on("unhandledRejection", (error) => {
  console.error("unhandledRejection:", error);
});

const airports = [
  ["LTAC", "ESB", "Ankara", "Esenboğa"],
  ["LTAD", "ANK", "Ankara", "Murted / Akinci"],
  ["LTAE", "ANK", "Ankara", "Akinci"],
  ["LTAF", "ADA", "Adana", "Şakirpaşa"],
  ["LTAH", "AFY", "Afyon", "Afyon"],
  ["LTAI", "AYT", "Antalya", "Antalya"],
  ["LTAJ", "GZT", "Gaziantep", "Oğuzeli"],
  ["LTAL", "KFS", "Kastamonu", "Kastamonu"],
  ["LTAN", "KYA", "Konya", "Konya"],
  ["LTAO", "N/A", "Turkey", "LTAO"],
  ["LTAP", "MZH", "Amasya", "Merzifon"],
  ["LTAR", "VAS", "Sivas", "Nuri Demirağ"],
  ["LTAS", "ONQ", "Zonguldak", "Çaycuma"],
  ["LTAT", "MLX", "Malatya", "Erhaç"],
  ["LTAU", "ASR", "Kayseri", "Erkilet"],
  ["LTAW", "TJK", "Tokat", "Tokat"],
  ["LTAY", "DNZ", "Denizli", "Çardak"],
  ["LTAZ", "NAV", "Nevşehir", "Kapadokya"],
  ["LTBA", "ISL", "İstanbul", "Atatürk"],
  ["LTBJ", "ADB", "Izmir", "Adnan Menderes"],
  ["LTBS", "DLM", "Mugla", "Dalaman"],
  ["LTFE", "BJV", "Mugla", "Milas-Bodrum"],
  ["LTFJ", "SAW", "İstanbul", "Sabiha Gökçen"],
  ["LTFM", "IST", "İstanbul", "İstanbul"],
  ["LTCC", "DIY", "Diyarbakır", "Diyarbakır"],
  ["LTCD", "ERC", "Erzincan", "Yildirim Akbulut"],
  ["LTCE", "ERZ", "Erzurum", "Erzurum"],
  ["LTCF", "KSY", "Kars", "Harakani"],
  ["LTCG", "TZX", "Trabzon", "Trabzon"],
  ["LTCI", "VAN", "Van", "Ferit Melen"],
  ["LTCJ", "BAL", "Batman", "Batman"],
  ["LTCK", "MSR", "Muş", "Sultan Alparslan"],
  ["LTCL", "SXZ", "Siirt", "Siirt"],
  ["LTCM", "NOP", "Sinop", "Sinop"],
  ["LTCN", "KCM", "Kahramanmaraş", "Kahramanmaraş"],
  ["LTCO", "AJI", "Ağrı", "Ahmed-i Hani"],
  ["LTCP", "ADF", "Adıyaman", "Adıyaman"],
  ["LTCR", "MQM", "Mardin", "Aziz Sancar"],
  ["LTCS", "GNY", "Şanlıurfa", "GAP"],
  ["LTCT", "IGD", "Iğdır", "Şehit Bülent Aydın"],
  ["LTCU", "BGG", "Bingöl", "Bingöl"],
  ["LTCV", "NKT", "Şırnak", "Şerafettin Elçi"],
  ["LTCW", "YKO", "Hakkari", "Yüksekova Selahaddin Eyyubi"],
  ["LTDA", "HTY", "Hatay", "Hatay"],
  ["LTDB", "N/A", "Turkey", "LTDB"],
  ["LTFA", "N/A", "İzmir", "Çiğli"],
  ["LTFB", "N/A", "İzmir", "Selçuk Efes"],
  ["LTFC", "ISE", "Isparta", "Süleyman Demirel"],
  ["LTFD", "EDO", "Balıkesir", "Koca Seyit"],
  ["LTFG", "GZP", "Antalya", "Gazipaşa-Alanya"],
  ["LTFH", "SZF", "Samsun", "Çarşamba"],
  ["LTBO", "USQ", "Uşak", "Uşak"],
  ["LTBQ", "KCO", "Kocaeli", "Cengiz Topel"],
  ["LTBR", "YEI", "Bursa", "Yenisehir"],
  ["LTBU", "TEQ", "Tekirdağ", "Çorlu Atatürk"],
  ["LTBZ", "KZR", "Kütahya", "Zafer"],
  ["LTCA", "EZS", "Elazığ", "Elazığ"]
].map(([icao, iata, city, name]) => ({ icao, iata, city, name }))
  .sort((a, b) => a.icao.localeCompare(b.icao));

const airportCoords = {
  LTAC: [40.128, 32.995], LTAD: [40.079, 32.565], LTAE: [40.078, 32.565],
  LTAF: [36.982, 35.280], LTAH: [38.726, 30.601], LTAI: [36.898, 30.800],
  LTAJ: [36.948, 37.479], LTAL: [41.315, 33.795], LTAN: [37.979, 32.562],
  LTAO: [38.353, 38.253], LTAP: [40.829, 35.522], LTAR: [39.813, 36.903],
  LTAS: [41.506, 32.089], LTAT: [38.435, 38.091], LTAU: [38.770, 35.495],
  LTAW: [40.307, 36.367], LTAY: [37.785, 29.701], LTAZ: [38.771, 34.534],
  LTBA: [40.976, 28.814], LTBJ: [38.292, 27.157], LTBS: [36.713, 28.793],
  LTFE: [37.250, 27.664], LTFJ: [40.898, 29.309], LTFM: [41.275, 28.752],
  LTCC: [37.894, 40.201], LTCD: [39.711, 39.527], LTCE: [39.956, 41.170],
  LTCF: [40.562, 43.115], LTCG: [40.995, 39.789], LTCI: [38.469, 43.332],
  LTCJ: [37.929, 41.116], LTCK: [38.747, 41.661], LTCL: [37.979, 41.840],
  LTCM: [42.015, 35.066], LTCN: [37.539, 36.953], LTCO: [39.654, 43.026],
  LTCP: [37.731, 38.469], LTCR: [37.223, 40.631], LTCS: [37.445, 38.895],
  LTCT: [39.976, 43.876], LTCU: [38.859, 40.592], LTCV: [37.364, 42.059],
  LTCW: [37.550, 44.238], LTDA: [36.362, 36.282], LTDB: [38.319, 27.160],
  LTFA: [38.514, 27.010], LTFB: [37.950, 27.329], LTFC: [37.855, 30.368],
  LTFD: [39.619, 27.926], LTFG: [36.299, 32.301], LTFH: [41.254, 36.567],
  LTBO: [38.682, 29.471], LTBQ: [40.735, 30.083], LTBR: [40.255, 29.562],
  LTBU: [41.138, 27.919], LTBZ: [39.111, 30.129], LTCA: [38.606, 39.291]
};

for (const airport of airports) {
  const coords = airportCoords[airport.icao];
  if (coords) {
    airport.lat = coords[0];
    airport.lon = coords[1];
  }
}

const allowedIcaos = new Set(airports.map((airport) => airport.icao));

const nameOrigins = {
  LTAC: "Adını Ankara yakınındaki Esenboğa yöresinden alır; isim tarihî kaynaklarda da geçen bir yer adıdır.",
  LTAD: "Mürted/Akıncı adı, meydanın bulunduğu bölge ve askerî havacılık geçmişiyle ilişkilidir.",
  LTAE: "Akıncı adı, Ankara'nın kuzeybatısındaki askerî havacılık bölgesiyle anılır.",
  LTAF: "Şakirpaşa adı, Adana'daki tarihî Şakirpaşa semti ve yerleşim alanından gelir.",
  LTAH: "Adını hizmet verdiği Afyonkarahisar bölgesinden alır.",
  LTAI: "Adını Türkiye'nin en önemli Akdeniz turizm merkezlerinden Antalya'dan alır.",
  LTAJ: "Oğuzeli adı, havalimanının Gaziantep'in Oğuzeli ilçesi yakınındaki konumundan gelir.",
  LTAL: "Adını hizmet verdiği Kastamonu kentinden alır.",
  LTAN: "Adını hizmet verdiği Konya kentinden alır.",
  LTAO: "Yerel havacılık/askerî kullanım karakteri olan bir meydandır; adlandırma bulunduğu saha kimliğiyle anılır.",
  LTAP: "Merzifon adı, Amasya'nın Merzifon ilçesindeki konumundan gelir.",
  LTAR: "Nuri Demirağ adı, Cumhuriyet döneminin önemli sanayici ve havacılık girişimcilerinden Nuri Demirağ'a atıftır.",
  LTAS: "Çaycuma adı, Zonguldak'ın Çaycuma ilçesi yakınındaki konumundan gelir.",
  LTAT: "Erhaç adı, Malatya yakınındaki yerel bölge adından gelir.",
  LTAU: "Erkilet adı, Kayseri'deki Erkilet yerleşimi ve meydan bölgesinden gelir.",
  LTAW: "Adını hizmet verdiği Tokat kentinden alır.",
  LTAY: "Çardak adı, Denizli'nin Çardak ilçesi yakınındaki konumundan gelir.",
  LTAZ: "Kapadokya adı, Nevşehir ve çevresindeki tarihî/coğrafi Kapadokya bölgesinden gelir.",
  LTBA: "Atatürk adı, Türkiye Cumhuriyeti'nin kurucusu Mustafa Kemal Atatürk'e atıftır.",
  LTBJ: "Adnan Menderes adı, Türkiye Cumhuriyeti'nin eski başbakanlarından Adnan Menderes'e atıftır.",
  LTBS: "Dalaman adı, Muğla'nın Dalaman ilçesindeki konumundan gelir.",
  LTFE: "Milas-Bodrum adı, Muğla'daki iki ana hizmet bölgesi olan Milas ve Bodrum'dan gelir.",
  LTFJ: "Sabiha Gökçen adı, dünyanın ilk kadın savaş pilotlarından biri olarak bilinen Sabiha Gökçen'e atıftır.",
  LTFM: "İstanbul adı, hizmet verdiği metropolün ana havalimanı kimliğini taşır.",
  LTCC: "Adını hizmet verdiği Diyarbakır kentinden alır.",
  LTCD: "Yıldırım Akbulut adı, Erzincanlı siyasetçi ve eski başbakan Yıldırım Akbulut'a atıftır.",
  LTCE: "Adını hizmet verdiği Erzurum kentinden alır.",
  LTCF: "Harakani adı, Kars ile özdeşleşen mutasavvıf Ebu'l Hasan Harakani'ye atıftır.",
  LTCG: "Adını hizmet verdiği Trabzon kentinden alır.",
  LTCI: "Ferit Melen adı, Vanlı siyasetçi ve eski başbakan Ferit Melen'e atıftır.",
  LTCJ: "Adını hizmet verdiği Batman kentinden alır.",
  LTCK: "Sultan Alparslan adı, Malazgirt ve Anadolu tarihiyle özdeşleşen Büyük Selçuklu hükümdarına atıftır.",
  LTCL: "Adını hizmet verdiği Siirt kentinden alır.",
  LTCM: "Adını hizmet verdiği Sinop kentinden alır.",
  LTCN: "Adını hizmet verdiği Kahramanmaraş kentinden alır.",
  LTCO: "Ahmed-i Hani adı, Doğu Anadolu kültür tarihinde önemli yeri olan şair ve düşünür Ahmed-i Hani'ye atıftır.",
  LTCP: "Adını hizmet verdiği Adıyaman kentinden alır.",
  LTCR: "Aziz Sancar adı, Nobel ödüllü bilim insanı Prof. Dr. Aziz Sancar'a atıftır.",
  LTCS: "GAP adı, Güneydoğu Anadolu Projesi'nin bölgesel kalkınma kimliğinden gelir.",
  LTCT: "Şehit Bülent Aydın adı, şehit güvenlik görevlisi Bülent Aydın'a atıftır.",
  LTCU: "Adını hizmet verdiği Bingöl kentinden alır.",
  LTCV: "Şerafettin Elçi adı, Şırnaklı siyasetçi Şerafettin Elçi'ye atıftır.",
  LTCW: "Selahaddin Eyyubi adı, bölge tarihindeki önemli tarihî figür Selahaddin Eyyubi'ye atıftır.",
  LTDA: "Adını hizmet verdiği Hatay kentinden alır.",
  LTDB: "Yerel saha kimliğiyle anılan bir İzmir bölgesi meydanıdır.",
  LTFA: "Çiğli adı, İzmir'in Çiğli ilçesindeki konumundan gelir.",
  LTFB: "Selçuk Efes adı, Selçuk ilçesi ve antik Efes bölgesine yakınlığından gelir.",
  LTFC: "Süleyman Demirel adı, Türkiye Cumhuriyeti'nin eski cumhurbaşkanlarından Süleyman Demirel'e atıftır.",
  LTFD: "Koca Seyit adı, Çanakkale Savaşı kahramanlarından Seyit Onbaşı'ya atıftır.",
  LTFG: "Gazipaşa-Alanya adı, Antalya'nın Gazipaşa ilçesi ve Alanya turizm bölgesinden gelir.",
  LTFH: "Çarşamba adı, Samsun'un Çarşamba ilçesi yakınındaki konumundan gelir.",
  LTBO: "Adını hizmet verdiği Uşak kentinden alır.",
  LTBQ: "Cengiz Topel adı, Kıbrıs harekâtı sırasında şehit olan pilot Yüzbaşı Cengiz Topel'e atıftır.",
  LTBR: "Yenişehir adı, Bursa'nın Yenişehir ilçesindeki konumundan gelir.",
  LTBU: "Çorlu Atatürk adı, Tekirdağ/Çorlu konumu ve Atatürk adına atıftan oluşur.",
  LTBZ: "Zafer adı, Kütahya-Afyon-Uşak bölgesinin Kurtuluş Savaşı hafızası ve bölgesel kimliğiyle ilişkilidir.",
  LTCA: "Adını hizmet verdiği Elazığ kentinden alır."
};

const trafficProfiles = {
  LTFM: "Çok yüksek hacimli uluslararası hub; geniş gövdeli uçuşlar, transit yolcu ve yoğun dalga operasyonları belirgindir.",
  LTAI: "Çok yüksek hacimli turizm meydanı; yaz sezonunda dış hat ve charter trafiği belirgin şekilde artar.",
  LTFJ: "Yüksek hacimli İstanbul meydanı; iç hat, dış hat ve düşük maliyetli taşıyıcı trafiği güçlüdür.",
  LTBJ: "Yüksek hacimli Ege meydanı; iç hat, dış hat ve yaz turizmi birlikte görülür.",
  LTAC: "Yüksek hacimli başkent meydanı; iç hat ağı, devlet trafiği ve dış hat bağlantıları birlikte çalışır.",
  LTBS: "Sezonluk dış hat/turizm trafiği güçlüdür; yaz aylarında charter ve Avrupa bağlantıları artar.",
  LTFE: "Sezonluk turizm trafiği güçlüdür; Bodrum ve çevresine yönelik yaz dış hat akışı belirgindir.",
  LTFG: "Turizm odaklı orta hacimli meydandır; Alanya/Gazipaşa bölgesine hizmet verir.",
  LTCG: "Karadeniz'in önemli bölgesel meydanlarından biridir; iç hat trafiği güçlü, dönemsel dış hat trafiği de görülebilir.",
  LTAJ: "Güneydoğu'nun yoğun bölgesel meydanlarından biridir; iç hat ve dış hat bağlantıları birlikte bulunur.",
  LTAF: "Adana bölgesi için tarihsel olarak yoğun iç hat/dış hat karakteri olan bir meydandır.",
  LTDA: "Bölgesel ve dönemsel dış hat/turizm/akraba ziyareti trafiği görülebilir.",
  defaultMilitary: "Sivil yolcu trafiği sınırlı veya askerî/özel kullanım karakteri baskındır; operasyonel kullanım bilgileri ayrıca doğrulanmalıdır.",
  defaultRegional: "Bölgesel yolcu trafiği ağırlıklıdır; iç hat bağlantıları, dönemsel talep ve yerel ekonomik hareketlilik belirleyicidir."
};

const militaryLike = new Set(["LTAD", "LTAE", "LTAH", "LTAO", "LTAP", "LTAT", "LTFA", "LTDB"]);

function geographyProfile(airport) {
  const { lat, lon, city } = airport;
  if (lon > 39.5 && lat > 38.5) return "Doğu Anadolu/Kuzeydoğu Anadolu karakteri taşır; yüksek rakım, dağlık çevre, kış koşulları ve buzlanma farkındalığı önemlidir.";
  if (lon > 39.0 && lat <= 38.5) return "Güneydoğu Anadolu platosu etkisindedir; yaz sıcakları, görüş/toz ve yüksek sıcaklık performansı yaklaşma brifinginde düşünülür.";
  if (lat > 40.7 && lon > 32) return "Karadeniz kuşağına yakındır; nem, yağış, düşük bulut tabanı ve kıyı-dağ geçişleri yaklaşma farkındalığı yaratır.";
  if (lon < 30.5 && lat < 39.5) return "Ege/Akdeniz kıyı etkilerine yakın bir meydandır; deniz meltemi, yaz sıcakları ve çevredeki tepelik arazi dikkate alınır.";
  if (lon < 31.5 && lat >= 39.5) return "Marmara/Ege geçiş bölgesindedir; deniz etkili hava, şehirleşme ve tepelik arazi birlikte değerlendirilebilir.";
  if (city === "İstanbul") return "Marmara havzasında, deniz etkili hava ve yoğun terminal sahası karakteri öne çıkar.";
  if (city === "Antalya" || city === "Muğla") return "Akdeniz/Ege turizm kıyısına yakın konumu nedeniyle deniz etkisi, dağlık çevre ve yaz sıcaklığı birlikte değerlendirilir.";
  return "İç Anadolu veya geçiş kuşağı karakteri taşır; geniş plato, rakım, mevsimsel rüzgâr ve kış şartları yaklaşma farkındalığında önemlidir.";
}

function airportProfile(icao, lang = "tr") {
  const airport = airports.find((item) => item.icao === icao);
  const traffic = trafficProfiles[icao] || (militaryLike.has(icao) ? trafficProfiles.defaultMilitary : trafficProfiles.defaultRegional);
  const profile = {
    nameOrigin: nameOrigins[icao] || `Adını hizmet verdiği ${airport?.city || "bölge"} çevresinden alır.`,
    traffic,
    geography: geographyProfile(airport),
    statsSource: "Güncel kesin yolcu sayıları için DHMİ İstatistikler sayfası esas alınmalıdır."
  };
  if (lang === "en") {
    return {
      nameOrigin: "The Turkish profile explains the local name origin; a full English name-origin layer can be expanded later.",
      traffic: "Traffic profile is qualitative. For exact current passenger figures, use the official DHMI statistics page.",
      geography: profile.geography,
      statsSource: "Use the official DHMI Statistics page for current passenger totals."
    };
  }
  return profile;
}

const airportBriefs = {
  LTAC: {
    terrain: "İç Anadolu platosunda, nispeten açık arazi karakteri. Kış şartları, düşük görüş ve buzlanma farkındalığı önemlidir.",
    approach: "Ankara bölgesi yoğun devlet/askeri trafik dokusuna yakın olabilir; chart notları, altitude restriction ve missed approach ayrımı dikkat ister.",
    culture: "Esenboğa adı, Ankara Savaşı'nda da anılan tarihî bir bölge adından gelir.",
    terrainEn: "Located on the Central Anatolian plateau, with relatively open surrounding terrain. Winter weather, low visibility, and icing awareness matter.",
    approachEn: "The Ankara area can have a complex civil/state/military traffic environment; chart notes, altitude restrictions, and missed approach details deserve careful briefing.",
    cultureEn: "The name Esenboğa comes from a historical regional name also associated with the Battle of Ankara."
  },
  LTFM: {
    terrain: "Karadeniz'e yakın, geniş ve açık arazi üzerinde büyük bir meydan. Rüzgâr, yağış hatları ve deniz etkili hava değişimleri belirgin olabilir.",
    approach: "Çok pistli ve yoğun terminal yapısı nedeniyle chart başlığı, pist numarası, transition ve ATC clearance uyumu kritik okuma başlıklarıdır.",
    culture: "İstanbul Havalimanı, Avrupa-Asya transfer trafiğinin en büyük merkezlerinden biridir.",
    terrainEn: "A large airport on open terrain near the Black Sea. Wind, precipitation bands, and maritime weather changes can be prominent.",
    approachEn: "Because of the multi-runway, high-density terminal environment, chart title, runway, transition, and ATC clearance alignment are critical.",
    cultureEn: "Istanbul Airport is one of the largest Europe-Asia transfer hubs."
  },
  LTFJ: {
    terrain: "Marmara'nın doğusunda, şehirleşme ve tepeli arazi etkileri olan bir bölgede yer alır. Kuzey-güney hava değişimleri hızlı hissedilebilir.",
    approach: "Yoğun trafik ve paralel İstanbul operasyonları nedeniyle arrival/approach ayrımı ve pist değişiklikleri iyi takip edilir.",
    culture: "Sabiha Gökçen, dünyanın ilk kadın savaş pilotlarından biri olarak bilinir.",
    terrainEn: "Located on the eastern side of the Marmara region, with urban and hilly terrain influences.",
    approachEn: "With dense traffic and parallel Istanbul operations, arrival/approach distinction and runway changes should be tracked carefully.",
    cultureEn: "Sabiha Gokcen is known as one of the world's first female combat pilots."
  },
  LTBJ: {
    terrain: "Ege kiyisina yakin, deniz etkili ruzgar ve sicak yaz termikleri gorulebilir. Cevrede tepelik arazi ve sehir dokusu vardir.",
    approach: "Izmir yaklasmalarinda pist, deniz/karasal referanslar ve published altitude basamaklari birlikte okunmali.",
    culture: "Adnan Menderes Havalimani, Ege turizmi ve Izmir is trafigi icin ana kapidir."
  },
  LTAI: {
    terrain: "Akdeniz kıyısı ile Toros Dağları arasında yer alır. Denizden karaya geçiş, dağ etkisi ve yaz sıcağı performans farkındalığı yaratır.",
    approach: "Terrain farkındalığı, final segment stabilizasyonu ve missed approach tırmanış profili dikkatle okunur.",
    culture: "Antalya, Türkiye'nin en yoğun turizm kapılarından biridir; yaz sezonunda trafik çok artar.",
    terrainEn: "Located between the Mediterranean coast and the Taurus Mountains. Sea-to-land transition, mountain influence, and summer heat affect awareness.",
    approachEn: "Terrain awareness, final segment stabilization, and missed approach climb profile should be briefed carefully.",
    cultureEn: "Antalya is one of Turkey's busiest tourism gateways, especially in summer."
  },
  LTBS: {
    terrain: "Dalaman vadisi ve kiyisal/daglik Mugla cografyasi etkili. Cevrede yukselen arazi ve deniz meltemleri olabilir.",
    approach: "Yaklasma brifinginde terrain, step-down altitude ve missed approach rotasi ozellikle ayrilmali.",
    culture: "Dalaman, Fethiye ve Gocek gibi turizm bolgelerine ana hava kapisidir."
  },
  LTFE: {
    terrain: "Bodrum-Milas arasinda, Ege kiyisina yakin tepelik arazi. Ruzgar ve yaz sicagi operasyonel farkindalik ister.",
    approach: "Pist secimi, tepelik cevre ve published descent path birlikte okunur.",
    culture: "Bodrum bolgesi antik Karya tarihinin onemli merkezlerinden biridir."
  },
  LTCG: {
    terrain: "Karadeniz kiyisinda, deniz ile daglar arasinda dar bir cografya. Nem, yagis ve bulut tabani degisken olabilir.",
    approach: "Kiyisal yaklasma, terrain ve missed approach talimati brifingin ana noktalaridir.",
    culture: "Trabzon, tarihi Ipek Yolu ve Karadeniz ticaretiyle anilan eski bir liman kentidir."
  },
  LTAU: {
    terrain: "Yuksek plato ve Erciyes Dagi etkisi. Rakim, sicaklik ve dag kaynakli hava kosullari farkindalik ister.",
    approach: "Yuksek meydan karakteri nedeniyle altitude, temperature ve performans notlari chart okumasinda one cikar.",
    culture: "Kayseri, Erciyes ve Kapadokya bolgesine yakinligi ile bilinir."
  },
  LTAZ: {
    terrain: "Kapadokya platosu; vadiler, yukseltiler ve volkanik arazi sekilleri bolgenin karakteridir.",
    approach: "Terrain ve step-down altitude farkindaligi, ozellikle dusuk goruste onemlidir.",
    culture: "Kapadokya peribacalari ve balon operasyonlariyla dunyaca bilinir."
  },
  LTCE: {
    terrain: "Dogu Anadolu'da yuksek rakimli ve daglik cevre. Kisin kar, buzlanma ve dusuk sicaklik etkili olabilir.",
    approach: "Yuksek rakim, terrain clearance ve missed approach tirmanis gereklilikleri dikkatle okunmali.",
    culture: "Erzurum, kisin sert iklimi ve kis sporlariyla bilinir."
  },
  LTCI: {
    terrain: "Van Golu havzasi ve yuksek daglik cevre. Gorsel referanslar guzel ama meteoroloji hizli degisebilir.",
    approach: "Terrain, rakim ve published altitude limitleri brifingde erken ele alinmali.",
    culture: "Van Golu, Turkiye'nin en buyuk goludur."
  },
  LTCR: {
    terrain: "Mezopotamya platosu kenarinda, sicak ve kuru yaz kosullari belirgin olabilir.",
    approach: "Sicak hava performansi, gorus/toz ve published altitude basamaklari dikkat ister.",
    culture: "Mardin, tas mimarisi ve tarihi dokusuyla meshurdur."
  },
  LTDA: {
    terrain: "Akdeniz dogusu, Amanos daglari ve kiyisal hava etkileri olan bir bolge.",
    approach: "Terrain ve meteoroloji notlari, ozellikle dusuk bulut ve yagisli kosullarda one cikar.",
    culture: "Hatay, cok katmanli mutfak ve tarih kulturuyle bilinir."
  }
};

function airportInfo(icao, lang = "tr") {
  const airport = airports.find((item) => item.icao === icao);
  const specific = airportBriefs[icao] || {};
  const profile = airportProfile(icao, lang);
  if (lang === "en") {
    return {
      airport,
      terrain: specific.terrainEn || "No airport-specific terrain note has been added yet. For approach awareness, review surrounding terrain, airport elevation, runway orientation, MSA, step-down altitudes, and the missed approach track together.",
      approach: specific.approachEn || "For approach briefing, read the chart title, procedure type, IAF/IF/FAF, profile altitudes, minimums, and missed approach section in order.",
      culture: specific.cultureEn || `${airport?.city || "This region"} can be expanded later with airport-specific cultural notes.`,
      profile
    };
  }
  return {
    airport,
    terrain: specific.terrain || "Bu meydan için özel not yok. Chart okurken çevre arazi, rakım, pist yönü, MSA, step-down irtifaları ve missed approach rotasını birlikte incele.",
    approach: specific.approach || "Yaklaşma için chart başlığı, procedure tipi, IAF/IF/FAF, profil irtifaları, minimumlar ve missed approach bölümlerini sırayla oku.",
    culture: specific.culture || profile.nameOrigin,
    profile
  };
}

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "content-length": Buffer.byteLength(body)
  });
  res.end(body);
}

function sendText(res, status, text) {
  res.writeHead(status, { "content-type": "text/plain; charset=utf-8" });
  res.end(text);
}

function isValidIcao(icao) {
  return /^LT[A-Z0-9]{2}$/.test(icao) && allowedIcaos.has(icao);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];
    if (quoted && char === "\"" && next === "\"") {
      value += "\"";
      i += 1;
    } else if (char === "\"") {
      quoted = !quoted;
    } else if (!quoted && char === ",") {
      row.push(value);
      value = "";
    } else if (!quoted && (char === "\n" || char === "\r")) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(value);
      if (row.some((cell) => cell !== "")) rows.push(row);
      row = [];
      value = "";
    } else {
      value += char;
    }
  }
  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }

  const headers = rows.shift() || [];
  return rows.map((items) => Object.fromEntries(headers.map((header, index) => [header, items[index] || ""])));
}

async function loadRunways() {
  if (runwayCache) return runwayCache;
  const response = await fetch("https://davidmegginson.github.io/ourairports-data/runways.csv");
  if (!response.ok) throw new Error("Pist verisi alınamadı.");
  const rows = parseCsv(await response.text());
  const byAirport = new Map();

  for (const row of rows) {
    const icao = row.airport_ident;
    if (!allowedIcaos.has(icao)) continue;
    const leHeading = Number(row.le_heading_degT || row.le_heading_deg);
    const heHeading = Number(row.he_heading_degT || row.he_heading_deg);
    const runway = {
      ident: row.le_ident && row.he_ident ? `${row.le_ident}/${row.he_ident}` : row.le_ident || row.he_ident || "RWY",
      le: row.le_ident || "",
      he: row.he_ident || "",
      heading: Number.isFinite(leHeading) ? leHeading : Number.isFinite(heHeading) ? (heHeading + 180) % 360 : null,
      reciprocalHeading: Number.isFinite(heHeading) ? heHeading : Number.isFinite(leHeading) ? (leHeading + 180) % 360 : null,
      lengthFt: Number(row.length_ft) || null,
      widthFt: Number(row.width_ft) || null,
      surface: row.surface || "",
      lighted: row.lighted === "1"
    };
    if (!byAirport.has(icao)) byAirport.set(icao, []);
    byAirport.get(icao).push(runway);
  }

  runwayCache = byAirport;
  return runwayCache;
}

function normalizeRunway(value) {
  return String(value || "").toUpperCase().replace(/^RWY\s*/, "").replace(/\s+/g, "");
}

function extractRunwaysFromText(text) {
  const found = new Set();
  const patterns = [
    /\bRWY\s*([0-3][0-9][LCR]?)\b/gi,
    /\bRUNWAY\s*([0-3][0-9][LCR]?)\b/gi,
    /\b(?:ILS|LOC|RNAV|VOR|NDB)[\s\/-]+(?:Z\s+|Y\s+|X\s+)?(?:RWY\s*)?([0-3][0-9][LCR]?)\b/gi
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text))) found.add(normalizeRunway(match[1]));
  }
  return [...found];
}

async function enrichChartsWithRunways(charts) {
  const missing = charts.filter((chart) => !runwayTagCache.has(chart.file));
  if (missing.length) {
    const texts = await extractPdfTexts(missing.map((chart) => chart.file));
    for (const chart of missing) {
      runwayTagCache.set(chart.file, extractRunwaysFromText(texts[chart.file] || ""));
    }
  }
  return charts.map((chart) => ({
    ...chart,
    runways: runwayTagCache.get(chart.file) || []
  }));
}

function pdfName(icao, number) {
  return `LT_AD_2_${icao}_IAC_${String(number).padStart(2, "0")}_en.pdf`;
}

async function pdfLooksValid(url) {
  const response = await fetch(url, { headers: { range: "bytes=0-7" } });
  if (!response.ok && response.status !== 206) return false;
  const contentType = (response.headers.get("content-type") || "").toLowerCase();
  const bytes = Buffer.from(await response.arrayBuffer());
  const signature = bytes.slice(0, 5).toString("latin1");
  return signature === "%PDF-" || (contentType.includes("pdf") && bytes.length > 0);
}

async function discoverCharts(icao) {
  const cached = chartCache.get(icao);
  if (cached && Date.now() - cached.time < CACHE_TTL_MS) return cached.charts;

  const probes = [];
  for (let i = 1; i <= PDF_SCAN_LIMIT; i += 1) {
    const file = pdfName(icao, i);
    probes.push({
      number: i,
      file,
      url: `${DHMI_BASE}/${file}`,
      source: "DHMI public AIP PDF"
    });
  }

  const results = [];
  const batchSize = 8;
  for (let index = 0; index < probes.length; index += batchSize) {
    const batch = probes.slice(index, index + batchSize);
    const checked = await Promise.all(batch.map(async (probe) => ({
      ...probe,
      ok: await pdfLooksValid(probe.url).catch(() => false)
    })));

    for (const item of checked) {
      if (!item.ok) continue;
      results.push({
        id: `IAC ${String(item.number).padStart(2, "0")}`,
        title: `Instrument Approach Chart ${String(item.number).padStart(2, "0")}`,
        file: item.file,
        viewerUrl: `/api/pdf/${item.file}`,
        sourceUrl: item.url,
        source: item.source
      });
    }
  }

  chartCache.set(icao, { time: Date.now(), charts: results });
  return results;
}

async function streamPdf(res, file) {
  if (!/^LT_AD_2_LT[A-Z0-9]{2}_IAC_\d{2}_en\.pdf$/.test(file)) {
    sendText(res, 400, "Bad PDF path");
    return;
  }

  const icao = file.match(/^LT_AD_2_(LT[A-Z0-9]{2})_/)[1];
  if (!isValidIcao(icao)) {
    sendText(res, 404, "Unknown Turkish airport");
    return;
  }

  const upstream = await fetch(`${DHMI_BASE}/${file}`);
  if (!upstream.ok) {
    sendText(res, upstream.status, "PDF not found");
    return;
  }

  const contentType = (upstream.headers.get("content-type") || "").toLowerCase();
  if (!contentType.includes("pdf")) {
    sendText(res, 415, "Not a displayable PDF");
    return;
  }

  res.writeHead(200, {
    "content-type": "application/pdf",
    "content-disposition": `inline; filename="${file}"`,
    "cache-control": "public, max-age=21600"
  });

  if (upstream.body?.pipeTo) {
    try {
      await upstream.body.pipeTo(Writable.toWeb(res));
    } catch (error) {
      if (!res.destroyed) res.destroy(error);
    }
  } else {
    res.end(Buffer.from(await upstream.arrayBuffer()));
  }
}

async function getPdfBuffer(file) {
  if (!/^LT_AD_2_LT[A-Z0-9]{2}_IAC_\d{2}_en\.pdf$/.test(file)) throw new Error("Bad PDF path");
  const icao = file.match(/^LT_AD_2_(LT[A-Z0-9]{2})_/)[1];
  if (!isValidIcao(icao)) throw new Error("Unknown Turkish airport");
  const response = await fetch(`${DHMI_BASE}/${file}`);
  if (!response.ok) throw new Error("PDF not found");
  const buffer = Buffer.from(await response.arrayBuffer());
  if (buffer.slice(0, 5).toString("latin1") !== "%PDF-") throw new Error("Not a readable PDF");
  return buffer;
}

async function extractPdfText(file) {
  const cached = textCache.get(file);
  if (cached) return cached;

  fs.mkdirSync(WORK_DIR, { recursive: true });
  const buffer = await getPdfBuffer(file);
  const tempPdf = path.join(WORK_DIR, `${file}.tmp.pdf`);
  const script = path.join(WORK_DIR, "extract_pdf_text.py");

  fs.writeFileSync(tempPdf, buffer);
  if (!fs.existsSync(script)) {
    fs.writeFileSync(script, [
      "import sys",
      "sys.stdout.reconfigure(encoding='utf-8', errors='replace')",
      "from pypdf import PdfReader",
      "reader = PdfReader(sys.argv[1])",
      "parts = []",
      "for page in reader.pages[:2]:",
      "    parts.append(page.extract_text() or '')",
      "print('\\n'.join(parts)[:12000])"
    ].join("\n"));
  }

  const result = spawnSync(PYTHON_EXE, [script, tempPdf], { encoding: "utf8", maxBuffer: 1024 * 1024 * 4 });
  try { fs.unlinkSync(tempPdf); } catch {}
  if (result.status !== 0) throw new Error(result.stderr || "PDF text extraction failed");

  const text = result.stdout.trim();
  textCache.set(file, text);
  return text;
}

async function extractPdfTexts(files) {
  const output = {};
  const missing = files.filter((file) => !textCache.has(file));
  for (const file of files) {
    if (textCache.has(file)) output[file] = textCache.get(file);
  }
  if (!missing.length) return output;

  fs.mkdirSync(WORK_DIR, { recursive: true });
  const runId = `${Date.now()}_${Math.random().toString(16).slice(2)}`;
  const manifestPath = path.join(WORK_DIR, `pdf_manifest_${runId}.json`);
  const script = path.join(WORK_DIR, "extract_pdf_texts.py");

  const downloaded = await Promise.all(missing.map(async (file) => {
    try {
      const buffer = await getPdfBuffer(file);
      const tempPdf = path.join(WORK_DIR, `${runId}_${file}.tmp.pdf`);
      fs.writeFileSync(tempPdf, buffer);
      return { file, path: tempPdf };
    } catch {
      return null;
    }
  }));
  const items = downloaded.filter(Boolean);

  if (!fs.existsSync(script)) {
    fs.writeFileSync(script, [
      "import json, sys",
      "sys.stdout.reconfigure(encoding='utf-8', errors='replace')",
      "from pypdf import PdfReader",
      "with open(sys.argv[1], 'r', encoding='utf-8') as f:",
      "    items = json.load(f)",
      "out = {}",
      "for item in items:",
      "    try:",
      "        reader = PdfReader(item['path'])",
      "        parts = []",
      "        for page in reader.pages[:2]:",
      "            parts.append(page.extract_text() or '')",
      "        out[item['file']] = '\\n'.join(parts)[:12000]",
      "    except Exception:",
      "        out[item['file']] = ''",
      "print(json.dumps(out, ensure_ascii=False))"
    ].join("\n"));
  }

  fs.writeFileSync(manifestPath, JSON.stringify(items), "utf8");
  const result = spawnSync(PYTHON_EXE, [script, manifestPath], { encoding: "utf8", maxBuffer: 1024 * 1024 * 8 });
  try { fs.unlinkSync(manifestPath); } catch {}
  for (const item of items) {
    try { fs.unlinkSync(item.path); } catch {}
  }
  if (result.status !== 0) throw new Error(result.stderr || "PDF batch text extraction failed");

  const parsed = JSON.parse(result.stdout || "{}");
  for (const [file, text] of Object.entries(parsed)) {
    textCache.set(file, text || "");
    output[file] = text || "";
  }
  return output;
}

function findLines(text, patterns) {
  return text
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .filter((line) => patterns.some((pattern) => pattern.test(line)))
    .slice(0, 12);
}

async function assist(file, question, lang = "tr") {
  const text = await extractPdfText(file);
  const airport = file.match(/^LT_AD_2_(LT[A-Z0-9]{2})_/)[1];
  const chart = file.match(/IAC_(\d{2})/)[1];
  const context = airportInfo(airport, lang);
  const q = String(question || "").toUpperCase();
  const lines = findLines(text, [
    /ILS|LOC|RNAV|VOR|NDB|DME/i,
    /MISSED|APPROACH|CLIMB|HOLD/i,
    /IAF|IF|FAF|MAPT|MAP|THR|RWY/i,
    /ALT|FT|OCA|OCH|DA|DH|MDA|MDH|RVR|VIS/i,
    /FREQ|MHZ|COURSE|CRS|GP|GS/i
  ]);

  const answer = [];
  if (lang === "en") {
    answer.push(`${airport} IAC ${chart} - training-oriented chart reading help`);
    answer.push(`Airport awareness: ${context.terrain} ${context.approach}`);

    if (q.includes("BRIEF")) {
      answer.push("Briefing flow: chart title and runway, approach type, navigation/frequency/course, IAF/transition, profile altitudes, final segment, minimums, and missed approach.");
    } else if (q.includes("MIN") || q.includes("DA") || q.includes("MDA")) {
      answer.push("When reading minimums, check approach category, DA/DH or MDA/MDH, OCA/OCH, RVR/VIS, and any notes or temperature restrictions together.");
    } else if (q.includes("MISSED")) {
      answer.push("For missed approach, separate the initial climb, turn direction, target fix/holding, altitude, and any DME conditions.");
    } else if (q.includes("ILS") || q.includes("RNAV") || q.includes("VOR")) {
      answer.push("Confirm the procedure type from the chart title and plan/profile view. For ILS, LOC course, GP and frequency matter; for RNAV, waypoint order and altitude constraints matter.");
    } else {
      answer.push("General reading flow: start with the procedure title/runway, then plan view, profile view, minimums, and missed approach.");
    }
  } else {
    answer.push(`${airport} IAC ${chart} - eğitim amaçlı chart okuma yardımı`);
    answer.push(`Meydan farkındalığı: ${context.terrain} ${context.approach}`);

    if (q.includes("BRIEF")) {
      answer.push("Briefing akışı: chart başlığı ve pist, yaklaşma tipi, navigation/frequency/course, IAF/transition, profil irtifaları, final segment, minimumlar ve missed approach.");
    } else if (q.includes("MIN") || q.includes("DA") || q.includes("MDA")) {
      answer.push("Minimum okurken approach category, DA/DH veya MDA/MDH, OCA/OCH, RVR/VIS ve varsa note/temperature restriction satırlarını birlikte kontrol et.");
    } else if (q.includes("MISSED")) {
      answer.push("Missed approach için ilk tırmanış, dönüş yönü, gidilecek fix/holding, altitude ve DME koşullarını ayrı ayrı oku.");
    } else if (q.includes("ILS") || q.includes("RNAV") || q.includes("VOR")) {
      answer.push("Procedure tipini chart başlığından ve plan/profile view üzerindeki navaid/fix etiketlerinden doğrula. ILS ise LOC course, GP ve frequency; RNAV ise waypoint ve altitude constraint zinciri kritik.");
    } else {
      answer.push("Genel okuma: önce başlıktan procedure/pist bilgisini al, sonra plan view, profile view, minimums ve missed approach bölümlerini sırayla incele.");
    }
  }

  if (!text) {
    answer.push(lang === "en"
      ? "A machine-readable text layer could not be extracted from this PDF. Use the visual viewer for manual reading."
      : "Bu PDF'ten metin katmanı okunamadı. Görsel viewer açık kalır; manuel chart okuma gerekir.");
  } else if (lines.length) {
    answer.push(lang === "en" ? "Relevant lines detected from the PDF text:" : "PDF metninden yakalanan ilgili satırlar:");
    answer.push(lines.map((line) => `- ${line}`).join("\n"));
  } else {
    answer.push(lang === "en"
      ? "The PDF text was read, but key lines could not be separated reliably. Confirm visually on the chart."
      : "PDF metni okundu ama anahtar satırlar güvenilir şekilde ayrılamadı. Görsel chart üzerinden teyit et.");
  }

  answer.push(lang === "en"
    ? "Warning: This assistant is for training and briefing practice only. Current AIP, NOTAMs, ATC, and company procedures remain authoritative for real operations."
    : "Uyarı: Bu asistan eğitim ve brifing pratiği içindir; operasyonel uçuşta güncel AIP, NOTAM, ATC ve şirket prosedürleri esas alınmalıdır.");
  return { answer: answer.join("\n\n"), extractedTextPreview: text.slice(0, 1000) };
}

async function coverage() {
  const rows = [];
  for (const airport of airports) {
    const charts = await discoverCharts(airport.icao);
    rows.push({ ...airport, charts: charts.length });
  }
  return rows.filter((row) => row.charts > 0).sort((a, b) => b.charts - a.charts || a.icao.localeCompare(b.icao));
}

function serveStatic(res, pathname) {
  const filePath = pathname === "/" ? path.join(ROOT, "turkiye-chart-finder.html") : path.join(ROOT, pathname);
  if (!filePath.startsWith(ROOT)) {
    sendText(res, 403, "Forbidden");
    return;
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      sendText(res, 404, "Not found");
      return;
    }
    const type = filePath.endsWith(".html") ? "text/html; charset=utf-8" : "application/octet-stream";
    res.writeHead(200, { "content-type": type });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);

    if (url.pathname === "/api/airports") {
      sendJson(res, 200, { airports, sources: ["DHMI public AIP PDF", "Direct public PDF validation"] });
      return;
    }

    if (url.pathname === "/api/charts") {
      const icao = (url.searchParams.get("icao") || "").trim().toUpperCase();
      const runway = normalizeRunway(url.searchParams.get("runway") || "");
      if (!isValidIcao(icao)) {
        sendJson(res, 400, { error: "Only registered Turkey ICAO codes are supported." });
        return;
      }
      const airport = airports.find((item) => item.icao === icao);
      let charts = await discoverCharts(icao);
      if (runway) {
        charts = (await enrichChartsWithRunways(charts))
          .filter((chart) => chart.runways.includes(runway));
      }
      sendJson(res, 200, { airport, charts, runway: runway || null, source: "public validated PDFs" });
      return;
    }

    if (url.pathname === "/api/runways") {
      const icao = (url.searchParams.get("icao") || "").trim().toUpperCase();
      if (!isValidIcao(icao)) {
        sendJson(res, 400, { error: "Only registered Turkey ICAO codes are supported." });
        return;
      }
      const runways = (await loadRunways()).get(icao) || [];
      sendJson(res, 200, { airport: airports.find((item) => item.icao === icao), runways, source: "OurAirports open data" });
      return;
    }

    if (url.pathname === "/api/airport-info") {
      const icao = (url.searchParams.get("icao") || "").trim().toUpperCase();
      const lang = url.searchParams.get("lang") === "en" ? "en" : "tr";
      if (!isValidIcao(icao)) {
        sendJson(res, 400, { error: "Only registered Turkey ICAO codes are supported." });
        return;
      }
      sendJson(res, 200, airportInfo(icao, lang));
      return;
    }

    if (url.pathname === "/api/coverage") {
      sendJson(res, 200, { airports: await coverage() });
      return;
    }

    if (url.pathname === "/api/assist" && req.method === "POST") {
      let body = "";
      req.on("data", (chunk) => { body += chunk; });
      req.on("end", async () => {
        try {
          const payload = JSON.parse(body || "{}");
          const lang = payload.lang === "en" ? "en" : "tr";
          sendJson(res, 200, await assist(String(payload.file || ""), String(payload.question || ""), lang));
        } catch (error) {
          sendJson(res, 400, { error: error.message });
        }
      });
      return;
    }

    if (url.pathname.startsWith("/api/pdf/")) {
      await streamPdf(res, decodeURIComponent(url.pathname.slice("/api/pdf/".length)));
      return;
    }

    serveStatic(res, decodeURIComponent(url.pathname));
  } catch (error) {
    console.error("request error:", error);
    if (res.headersSent) {
      if (!res.destroyed) res.end();
      return;
    }
    sendJson(res, 500, { error: error.message });
  }
});

server.listen(PORT, () => {
  console.log(`Türkiye Chart Lab çalışıyor: http://tr-approach-chart-finder.local:${PORT}`);
});
