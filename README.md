# Batas wilayah Indonesia untuk peta MR KPU

GeoJSON ini memuat batas 38 provinsi dan 514 kabupaten/kota yang cocok dengan master satuan kerja KPU. Sumbernya adalah ekstrak OpenStreetMap Indonesia tanggal 9 Oktober 2026 dari Geofabrik (`indonesia-261009.osm.pbf`, MD5 `cd5c8d8208443bb7ef190a3ed41401aa`). Dua way anggota relasi yang tidak ikut dalam ekstrak dipulihkan dari OSM API; keduanya terakhir diubah sebelum tanggal snapshot. Lihat `DATA_LICENSE.md` untuk atribusi dan lisensi.

Data di `data/2026-10-09/MapProvince_ID_XX.geojson` mempertahankan seluruh titik batas kabupaten/kota OSM, tanpa penyederhanaan geometri. Peta nasional `MapNational.geojson` dibentuk dari gabungan daratan kabupaten/kota—bukan batas maritim provinsi—agar pulau-pulau tetap terpisah oleh laut. Hanya peta nasional ini disederhanakan pada skala tampilan (toleransi maksimal 0,0005 derajat) supaya pemuatan awal tetap ringan. `MapOutline.geojson` menyimpan garis pantai terpisah agar browser tidak menghitungnya ulang. `MapManifest.json` mencatat cakupan dan jumlah titik. Aplikasi memuat berkas provinsi hanya saat wilayah itu dibuka.

Dataset ini hanya berisi geometri dan identitas wilayah, tanpa data risiko KPU. Berkas dibuat oleh `tools/validate-osm-map.py` di proyek Dashboard MR KPU. Generator menghentikan proses bila pasangan wilayah terhadap master tidak tepat 38 provinsi dan 514 kabupaten/kota, ada ID ganda, atau geometri tidak valid.

GitHub Pages menyajikan data melalui URL `https://ahsa29.github.io/kpu-osm-boundaries-2026/data/2026-10-09/`. Untuk menjaga konsistensi aplikasi, versi tanggal ini tidak diubah setelah diterbitkan; pembaruan batas memakai direktori versi baru.
