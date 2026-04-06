# NAIK Frontend Files

## File Structure

```
NAIK/
├── templates/
│   └── NAIK.html       ← Main home page template (extends base.html)
├── static/
│   ├── naik.css        ← All styles for the home page
│   └── naik.js         ← Counter animation + mobile nav logic
└── README.md
```

## How to integrate into your Flask app

### 1. Move the files into your project

```
your-project/
├── templates/
│   ├── base.html           ← your existing base
│   └── NAIK.html           ← add this
├── static/
│   ├── styles.css          ← your existing styles (unchanged)
│   ├── naik.css            ← add this
│   └── naik.js             ← add this
└── app.py
```

### 2. Update your home route in app.py

```python
@app.route("/home")
def home():
    return render_template("NAIK.html")
```

### 3. That's it

`NAIK.html` already extends `base.html` and uses `url_for()` for all
internal links, so it will work with your existing Flask routes.

---

## Colour palette (CSS variables in naik.css)

| Variable    | Hex       | Used for                        |
|-------------|-----------|---------------------------------|
| `--red`     | `#BF4646` | Primary actions, headings       |
| `--teal`    | `#7EACB5` | Secondary accent                |
| `--peach`   | `#EDDCC6` | Warm surface / card backgrounds |
| `--cream`   | `#FFF4EA` | Page background                 |
| `--rose`    | `#D4738A` | For Her section                 |
| `--ink`     | `#1c1713` | Body text                       |

---

## Updating the stats counter (naik.js)

Find these lines near the bottom of `naik.js` and swap in real numbers:

```js
animateCount('stat-users',    12400, 1800);   // total users
animateCount('stat-success',  73,    1600);   // % success rate
animateCount('stat-states',   14,    1200);   // states covered
animateCount('stat-earnings', 750,   1800);   // avg RM earned
```

---

## Adding real team photos

In `NAIK.html`, find the team section and replace the `.avatar` div
with a real image:

```html
<!-- Before -->
<div class="avatar av-red">C</div>

<!-- After -->
<img src="{{ url_for('static', filename='images/camelia.jpg') }}"
     alt="Camelia"
     style="width:72px; height:72px; border-radius:50%; object-fit:cover; margin:0 auto 1rem; display:block;">
```
