# nlp_model.py

def predict_issue_by_merk(keluhan, merk):
    keluhan = keluhan.lower()
    merk = merk.lower()

    rules = [
        (["layar", "retak", "pecah"], "Layar rusak / pecah", 250000),
        (["lcd", "blank", "hitam", "mati total"], "LCD bermasalah", 300000),
        (["baterai", "baterai cepat habis", "daya", "boros"], "Masalah baterai", 180000),
        (["sinyal", "tidak ada sinyal", "jaringan"], "IC sinyal rusak", 200000),
        (["charger", "cas", "tidak bisa cas", "colokan", "port"], "Port charger rusak", 150000),
        (["kamera", "blur", "tidak bisa foto"], "Kamera rusak", 220000),
        (["panas", "overheat"], "HP overheat / kepanasan", 190000),
        (["lambat", "lemot", "hang"], "Performa lambat / butuh reset", 100000),
        (["speaker", "suara", "tidak ada suara"], "Speaker rusak", 160000),
        (["mic", "tidak bisa nelpon", "lawan bicara tidak dengar"], "Mic rusak", 150000),
    ]

    for keywords, diagnosis, harga in rules:
        if any(keyword in keluhan for keyword in keywords):
            harga_adjusted = harga
            if "iphone" in merk:
                harga_adjusted += 100000
            return diagnosis, harga_adjusted

    return "Kerusakan tidak dikenali, perlu pengecekan langsung", 100000
