# Batas wilayah Indonesia untuk peta MR KPU

GeoJSON ini memuat batas 38 provinsi dan 514 kabupaten/kota yang cocok dengan master satuan kerja KPU. Sumbernya adalah ekstrak OpenStreetMap Indonesia tanggal 9 Oktober 2026 dari Geofabrik (`indonesia-261009.osm.pbf`, MD5 `cd5c8d8208443bb7ef190a3ed41401aa`). Dua way anggota relasi yang tidak ikut dalam ekstrak dipulihkan dari OSM API; keduanya terakhir diubah sebelum tanggal snapshot. Lihat `DATA_LICENSE.md` untuk atribusi dan lisensi.

Data di `data/2026-10-10/MapProvince_ID_XX.geojson` mempertahankan titik batas kabupaten/kota OSM; untuk Sumatera Utara, poligon administratif yang mencakup laut di sekitar Nias dipotong dengan [poligon daratan OSM](https://osmdata.openstreetmap.de/data/land-polygons.html) yang diambil 10 Oktober 2026. Koreksi itu memisahkan Nias, Kepulauan Batu, dan daratan utama tanpa mengubah pasangan 33 kabupaten/kota. Peta nasional `MapNational.geojson` dibentuk dari gabungan geometri kabupaten/kota dan disederhanakan pada skala tampilan (toleransi maksimal 0,0005 derajat). `MapManifest.json` mencatat cakupan dan jumlah titik. Aplikasi memuat berkas provinsi hanya saat wilayah itu dibuka.

Dataset ini hanya berisi geometri dan identitas wilayah, tanpa data risiko KPU. Berkas dibuat oleh `tools/validate-osm-map.py` di proyek Dashboard MR KPU. Generator menghentikan proses bila pasangan wilayah terhadap master tidak tepat 38 provinsi dan 514 kabupaten/kota, ada ID ganda, atau geometri tidak valid.

GitHub Pages menyajikan data aktif melalui URL `https://ahsa29.github.io/kpu-osm-boundaries-2026/data/2026-10-10/`. Versi `2026-10-09` tetap tersedia tanpa perubahan. Koreksi Sumatera Utara dibuat dengan `tools/repair_sumut_land.py`; versi yang sudah terbit tidak ditimpa oleh pembaruan berikutnya.
