# วิธีรันโปรเจกต์ Food Roulette (Backend + Frontend)

คู่มือนี้พาไปถึงจุดที่ **แอป Flutter แสดงข้อมูลจริงจาก backend** ไม่ใช่ข้อมูลปลอมที่ฝังไว้ในโค้ด
อ่านหัวข้อ 4 กับ 6 ให้ดี — สองข้อนั้นคือจุดที่คนส่วนใหญ่พลาดแล้วเข้าใจผิดว่าต่อ API ติดแล้ว

ตรวจสอบกับ repo จริงเมื่อ 2026-08-01 (backend ถึง M2 / chat)

---

## 0. ต้องมีอะไรก่อน

| อย่าง | เวอร์ชัน | เช็คด้วย |
|------|---------|---------|
| Python | 3.11 ขึ้นไป (ทดสอบบน 3.13) | `python3 --version` |
| Flutter SDK | Dart `^3.12.2` | `flutter doctor` |
| อุปกรณ์ทดสอบ | Android emulator, iOS simulator, macOS desktop หรือ Chrome | `flutter devices` |
| sqlite3 | ติดมากับ macOS อยู่แล้ว | `sqlite3 --version` |

ไม่ต้องมี Gemini API key ก็รันได้ทั้งระบบ (ดูหัวข้อ 3)

---

## 1. เตรียม Backend (ทำครั้งเดียว)

ทุกคำสั่งในหัวข้อนี้รันจากโฟลเดอร์ **`backend/`**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

โหลดข้อมูลร้าน/เมนูเข้า SQLite:

```bash
python -m app.ingest
```

ต้องได้ผลแบบนี้ ถ้าตัวเลขไม่ตรงแปลว่าอ่านไฟล์ JSON ไม่เจอ:

```
  restaurants : 50
  menu_items  : 1250
  price bands : 50 derived from menu medians
  FK integrity: OK (no orphan menu_items)
```

คำสั่งนี้รันซ้ำได้ตลอด (idempotent) — สร้างตารางร้าน/เมนูใหม่ แต่ **ไม่ลบ** ข้อมูลผู้ใช้

---

## 2. รัน Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0
```

> **`--host 0.0.0.0` สำคัญมาก** — ถ้าไม่ใส่ Android emulator กับมือถือจริงจะยิงเข้าไม่ได้

เปิดเช็คในเบราว์เซอร์:

| URL | ได้อะไร |
|-----|--------|
| http://127.0.0.1:8000/health | สถานะ + จำนวนแถว (ยืนยันว่า ingest สำเร็จ) |
| http://127.0.0.1:8000/docs | Swagger UI — ลองยิงทุก endpoint ได้จากหน้านี้ |

`/health` ต้องขึ้น `"restaurants":50,"menu_items":1250` ถ้าเป็น `0` แปลว่ายังไม่ได้รันข้อ 1

---

## 3. Gemini key (ข้ามได้)

แชทเขียนคำตอบด้วย Gemini แต่ **ไม่มี key ก็ยังใช้งานได้**: `/chat` จะข้าม Gemini แล้วส่ง
ร้านที่ผ่านตัวกรองกลับมาเหมือนเดิม พร้อมบอกว่า `degraded: "LLM_UNAVAILABLE"`

ถ้าจะให้มีข้อความตอบเป็นภาษาคน:

```bash
cp .env.example .env               # แล้วเปิดใส่ค่า GEMINI_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --env-file .env
```

`.env` อยู่ใน `.gitignore` — **อย่า commit key** และฝั่ง Flutter ไม่ต้องรู้จัก key เลย

---

## 4. ⚠️ สร้าง user id `"1"` — ถ้าไม่ทำ แอปจะโชว์ข้อมูลปลอม

ตอนนี้ `lib/state/providers.dart` ยิง API ด้วย `user_id` ที่ฝังไว้ว่า `"1"` แต่ `POST /auth/session`
ของ backend แจก id เป็น uuid ยาว ๆ เสมอ ผลคือ backend ตอบ `404 NOT_FOUND` แล้วโค้ดฝั่งแอป
`catch (_) {}` กลืน error ทิ้ง แล้ว **แสดงข้อมูลปลอมที่เขียนไว้ในไฟล์แทน** โดยไม่ขึ้น error อะไรเลย

ทางแก้ชั่วคราวจนกว่า frontend จะต่อ `/auth/session` จริง — เพิ่มผู้ใช้ id `1` เข้า DB ตรง ๆ:

```bash
# รันจาก backend/
sqlite3 food_roulette.db \
  "INSERT OR IGNORE INTO users (id, display_name, created_at) VALUES ('1','demo',datetime('now'));"
```

เช็คว่าใช้ได้แล้ว (ต้องได้รายชื่อร้าน ไม่ใช่ `NOT_FOUND`):

```bash
curl -s localhost:8000/recommend -H 'content-type: application/json' \
  -d '{"user_id":"1","limit":2}'
```

ทำครั้งเดียวพอ อยู่ถาวรใน `food_roulette.db` และ `python -m app.ingest` ไม่ลบทิ้ง

---

## 5. รัน Frontend

เปิด terminal **หน้าต่างใหม่** (ปล่อย uvicorn รันค้างไว้) แล้วรันจาก **root ของ repo**:

```bash
flutter pub get
flutter devices        # ดูว่ามีอุปกรณ์อะไรให้เลือกบ้าง
```

### ถ้าใช้ macOS desktop / iOS simulator / Chrome

ใช้ได้เลย เพราะโค้ดชี้ไปที่ `http://127.0.0.1:8000` อยู่แล้ว:

```bash
flutter run -d macos          # หรือ -d chrome / -d iphone
```

### ถ้าใช้ Android emulator

ข้างใน emulator คำว่า `127.0.0.1` หมายถึงตัว emulator เอง ไม่ใช่เครื่องเรา แต่ `providers.dart`
ฝัง `127.0.0.1` ไว้ตายตัว วิธีที่ง่ายที่สุดคือ **ไม่ต้องแก้โค้ด** แต่ต่อ port ผ่าน adb:

```bash
adb reverse tcp:8000 tcp:8000     # รันทุกครั้งหลังเปิด emulator
flutter run -d emulator-5554
```

(อีกทางคือแก้ `lib/state/providers.dart` บรรทัด 14 เป็น `http://10.0.2.2:8000` แต่ต้องระวัง
ตอน commit เพราะจะทำให้ desktop/simulator ใช้ไม่ได้แทน)

---

## 6. ดูยังไงว่าเห็น "ข้อมูลจริง" แล้ว

จุดนี้สำคัญ เพราะแอปหน้าตาเหมือนกันทั้งสองกรณี:

| สิ่งที่เห็นบนการ์ด | แปลว่า |
|-------------------|--------|
| `Matthew's`, `เรสเตอร์ เดย์` และมี **ดาวคะแนน 4.7 / 3.4** | ❌ ข้อมูลปลอมในโค้ด — backend ยิงไม่ติด |
| ชื่อร้านแถว มธ. เช่น `People Haus กาแฟ อาหาร @มธ รังสิต`, `ดงมาชิ`, `S.O.L.A.R Café` และ **ไม่มีดาว** | ✅ ข้อมูลจริงจาก backend |

เหตุผลที่ดูจากดาวได้: backend ส่ง `rating: null` เสมอจนกว่าจะถึง M4 (Google Places)
ถ้าเห็นดาว แปลว่าไม่ได้มาจาก backend แน่นอน

ยืนยันซ้ำอีกทางคือดู log ของ uvicorn — ต้องมีบรรทัดแบบนี้วิ่งตอนเปิดแอป:

```
INFO:  127.0.0.1 - "POST /recommend HTTP/1.1" 200 OK
```

ถ้าขึ้น `404 Not Found` แปลว่ายังไม่ได้ทำข้อ 4

---

## 7. ลองใช้งานจริงทั้งเส้น

1. เปิดแอป → หน้าแชท (`/chat`) จะโหลดการ์ดร้านขึ้นมา
2. กดรูปคนมุมขวาบน → หน้าโปรไฟล์
3. เลือกข้อจำกัด เช่น **แพ้ถั่วลิสง (peanuts)** แล้วบันทึก
4. กลับหน้าแรก → การ์ดต้องเปลี่ยนชุด และตัวเลข "กรองออกไป N เมนู" ต้องขยับ
5. ดู log uvicorn ต้องเห็น `PUT /users/1/preferences 200` ตามด้วย `POST /recommend 200`

เมนูที่มีถั่วจะหายไปทั้งหมด — การกรองทำใน SQL ฝั่ง backend ฝั่งแอปไม่มีสิทธิ์ตัดสินใจเรื่องความปลอดภัย

---

## 8. ทดสอบแชท (`POST /chat`)

**ตอนนี้ช่องพิมพ์ในแอปยังไม่ได้ต่อกับ `/chat`** (เป็นงาน M2 ฝั่ง frontend ที่ยังไม่ทำ)
หน้าแชทดึงข้อมูลจาก `/recommend` อย่างเดียว ถ้าจะทดสอบแชทตอนนี้ให้ใช้ Swagger ที่
http://127.0.0.1:8000/docs หรือ curl:

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' -d '{
  "user_id": "1", "text": "อยากกินอะไรเผ็ดๆ ไม่เอาหมู",
  "latitude": 14.07, "longitude": 100.604, "limit": 3 }' | python3 -m json.tool
```

สิ่งที่ควรเห็น:

- `reply` เป็นข้อความไทย ที่พูดถึง**เฉพาะร้านที่อยู่ใน `recommendations`** เท่านั้น
- `degraded: null` ถ้าใส่ key แล้ว / `degraded: "LLM_UNAVAILABLE"` ถ้าไม่ได้ใส่ (การ์ดยังมาครบเหมือนเดิม)
- ไม่มีเมนูหมูอยู่ใน `safe_dishes` เลยสักจาน

ฝั่ง frontend ที่จะทำต่อ ใช้ไฟล์ตัวอย่างได้เลยโดยไม่ต้องเปิด backend:
`docs/api/fixtures/chat_with_cards.json`, `chat_no_cards.json`, `chat_degraded.json`

---

## 9. รันเทสต์ backend

```bash
cd backend && pytest          # 69 เทสต์ ไม่ถึงวินาที
```

ไม่ต้องมี key และไม่มีเทสต์ไหนยิงเน็ตจริง (Gemini ถูก stub ไว้ทั้งหมด)

---

## 10. ปัญหาที่เจอบ่อย

| อาการ | วิธีแก้ |
|------|--------|
| `ModuleNotFoundError: fastapi` | ยังไม่ได้ `source .venv/bin/activate` |
| `/health` ขึ้น `restaurants: 0` | ยังไม่ได้รัน `python -m app.ingest` |
| การ์ดขึ้นเป็น `Matthew's` + มีดาว | ยังไม่ได้ทำข้อ 4 (สร้าง user id `1`) |
| แอปบน emulator โหลดค้าง/ไม่มีข้อมูล | ลืม `adb reverse tcp:8000 tcp:8000` หรือลืม `--host 0.0.0.0` |
| port 8000 ถูกใช้อยู่ | `uvicorn app.main:app --port 8001` (แล้วแก้ base url ฝั่งแอปตาม) |
| `/chat` ตอบ `degraded: "LLM_UNAVAILABLE"` ตลอด | ยังไม่ได้ตั้ง `GEMINI_API_KEY` — ไม่ใช่บั๊ก ระบบตั้งใจให้ทำงานต่อได้ |
| `pytest` fail ที่ `test_fixtures.py` | มีคนแก้ schema แล้วไม่ได้ regen: `python -m tools.make_contract` |

---

## 11. สิ่งที่ยังไม่ได้เชื่อมกัน (ให้ทีมรู้ตรงกัน)

คู่มือนี้พาให้ "เห็นภาพรวมทำงานได้" แต่ของพวกนี้ยังค้างอยู่จริง ๆ ในโค้ด ไม่ใช่ตั้งค่าผิด:

1. **`lib/state/providers.dart` ไม่ได้ใช้ `AppConfig`** — ฝัง `http://127.0.0.1:8000` และ `user_id: "1"`
   ไว้ตรง ๆ ทำให้ flag `--dart-define=API_BASE_URL` และ `--dart-define=USE_MOCK` **ไม่มีผลใด ๆ**
   กับหน้าจอที่ใช้งานอยู่ตอนนี้ (`MockApi` / `HttpApi` ที่เขียนไว้ยังไม่มีหน้าไหนเรียกใช้เลย)
2. **`catch (_) {}` กลืน error ทุกชนิด** แล้ว fallback เป็นข้อมูลปลอม ทำให้ backend ตายอยู่ก็ดูเหมือนแอปปกติ
   — ควรเปลี่ยนเป็นแสดง error state ตาม ROADMAP §3.2
3. **ยังไม่มีการเรียก `POST /auth/session`** จึงต้อง seed user `"1"` เองตามข้อ 4
4. **`HardConstraints` ฝั่ง Flutter ยังไม่มี `no_pork`** ที่ backend เพิ่มไปแล้ว — ถ้ากดบันทึกโปรไฟล์
   ค่านี้จะถูกเซ็ตกลับเป็น false ทุกครั้ง
5. **ช่องพิมพ์แชทยังไม่ยิง `POST /chat`** (M2 ฝั่ง frontend)

รายละเอียดสถานะแต่ละ milestone อยู่ใน `ROADMAP.md` §0 และ §4
