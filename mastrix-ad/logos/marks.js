// 20 Mastrix Media marks. Each mark draws into a 200x200 viewBox from a palette,
// so the same geometry renders the hero, the profile-picture test and the inverse test.
window.PALETTES = {
  dark: { bg: "#0B231C", fg: "#EEE6D6", accent: "#C9A86A", dim: "rgba(238,230,214,.3)" },
  light: { bg: "#EEE6D6", fg: "#0B231C", accent: "#9A7636", dim: "rgba(11,35,28,.28)" },
};

const pts = (a) => a.map((p) => p.join(",")).join(" ");
const stroke = (color, w, extra = "") =>
  `fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" ${extra}`;
let uidCounter = 0;
const uid = (k) => `${k}-${++uidCounter}`;

function dotGrid(rows, gap, origin, draw) {
  let out = "";
  rows.forEach((row, r) => [...row].forEach((ch, c) => { out += draw(ch, origin + c * gap, origin + r * gap, r, c); }));
  return out;
}

const M_ROWS = ["X.....X", "XX...XX", "X.X.X.X", "X..X..X", "X.....X", "X.....X", "X.....X"];

window.MARKS = [
  // ---------- 1. The matrix ----------
  {
    n: 1, name: "نقطة الماتركس", idea: "نقاط الجمهور بتتجمّع وبتشكّل M، نفس فكرة الإعلان",
    svg: (p) => dotGrid(M_ROWS, 22, 34, (ch, x, y, r, c) => ch === "X"
      ? `<circle cx="${x}" cy="${y}" r="${r === 3 && c === 3 ? 9.5 : 7}" fill="${r === 3 && c === 3 ? p.fg : p.accent}"/>`
      : `<circle cx="${x}" cy="${y}" r="2.4" fill="${p.dim}"/>`),
  },
  {
    n: 2, name: "الخلية", idea: "M من خلايا مصفوفة، وخلية وحدة نحاسية هي الزبون",
    svg: (p) => dotGrid(["X...X", "XX.XX", "X.X.X", "X...X", "X...X"], 33, 21, (ch, x, y, r, c) => ch === "X"
      ? `<rect x="${x}" y="${y}" width="26" height="26" rx="5" fill="${r === 2 && c === 2 ? p.accent : p.fg}"/>`
      : `<rect x="${x + 0.75}" y="${y + 0.75}" width="24.5" height="24.5" rx="5" fill="none" stroke="${p.dim}" stroke-width="1.5"/>`),
  },
  {
    n: 3, name: "الواحد", idea: "من بين 16 نقطة، إحنا منلاقي الزبون الصح",
    svg: (p) => dotGrid(["....", "....", "....", "...."], 38, 43, (ch, x, y, r, c) => r === 1 && c === 2
      ? `<circle cx="${x}" cy="${y}" r="23" ${stroke(p.accent, 2.5, 'opacity=".6"')}/><circle cx="${x}" cy="${y}" r="12" fill="${p.accent}"/>`
      : `<circle cx="${x}" cy="${y}" r="5.5" fill="${p.fg}" opacity=".45"/>`),
  },
  {
    n: 4, name: "التحوّل", idea: "جمهور مبعثر تحت، وحرف صلب فوق: من مشاهدات لنتيجة",
    svg: (p) => [[40, 162, 3], [40, 140, 4.2], [40, 118, 5.4], [40, 96, 6.6]]
      .map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${p.accent}"/>`).join("")
      + `<polyline points="40,78 40,44 100,114 160,44 160,162" ${stroke(p.fg, 16)}/>`,
  },

  // ---------- 2. The conversation ----------
  {
    n: 5, name: "الفقاعة", idea: "فقاعة محادثة، والـM محفور فيها",
    svg: (p) => {
      const id = uid("m5");
      return `<mask id="${id}"><rect width="200" height="200" fill="#fff"/>
        <polyline points="64,124 64,66 100,106 136,66 136,124" fill="none" stroke="#000" stroke-width="15" stroke-linejoin="round" stroke-linecap="round"/></mask>
        <g mask="url(#${id})"><rect x="24" y="28" width="152" height="124" rx="36" fill="${p.accent}"/>
        <path d="M52,146 L42,180 L90,148 Z" fill="${p.accent}"/></g>`;
    },
  },
  {
    n: 6, name: "ذيل المحادثة", idea: "حرف m بينتهي بذيل فقاعة محادثة",
    svg: (p) => `<path d="M40,148 V90 A30,30 0 0 1 100,90 V148 M100,90 A30,30 0 0 1 160,90 V134" ${stroke(p.fg, 15)}/>
      <path d="M160,134 Q160,156 184,162" ${stroke(p.accent, 15)}/>`,
  },
  {
    n: 7, name: "عم يكتب", idea: "«عم يكتب…» بس النقاط طالعة لفوق: محادثة بتكبر",
    svg: (p) => `<path d="M72,46 H128 A50,50 0 0 1 153,139.3 L164,172 L122,146 H72 A50,50 0 0 1 72,46 Z" ${stroke(p.fg, 8)}/>
      <circle cx="68" cy="104" r="9" fill="${p.fg}" opacity=".5"/>
      <circle cx="100" cy="96" r="11" fill="${p.fg}"/>
      <circle cx="132" cy="88" r="13" fill="${p.accent}"/>`,
  },
  {
    n: 8, name: "ميم", idea: "حرف «م» العربي هو نفسه فقاعة محادثة بذيل",
    svg: (p) => `<circle cx="114" cy="80" r="42" ${stroke(p.fg, 17)}/>
      <path d="M74.5,94.4 C67,122 68,152 78,180" ${stroke(p.fg, 17)}/>
      <circle cx="114" cy="80" r="11" fill="${p.accent}"/>`,
  },

  // ---------- 3. Growth ----------
  {
    n: 9, name: "الخط الطالع", idea: "الـM هو نفسه خط مبيعات طالع",
    svg: (p) => `<line x1="24" y1="178" x2="176" y2="178" stroke="${p.dim}" stroke-width="2.5"/>
      <polyline points="30,160 70,76 102,124 150,42" ${stroke(p.fg, 17)}/>
      <circle cx="150" cy="42" r="13" fill="${p.accent}"/>`,
  },
  {
    n: 10, name: "الأعمدة", idea: "M من أعمدة رسم بياني، وآخر عمود هو الأعلى",
    svg: (p) => [116, 78, 44, 90, 140].map((h, i) =>
      `<rect x="${27 + i * 31}" y="${172 - h}" width="22" height="${h}" rx="3" fill="${i === 4 ? p.accent : p.fg}"/>`).join(""),
  },
  {
    n: 11, name: "الصفقة", idea: "M بيخلص بإشارة ✓: صفقة مسكّرة",
    svg: (p) => `<polyline points="38,166 38,48 98,128" ${stroke(p.fg, 18)}/>
      <line x1="98" y1="128" x2="170" y2="32" ${stroke(p.accent, 18)}/>`,
  },
  {
    n: 12, name: "التاج", idea: "تلات قمم فوق بعض بتشكّل تاج: الريادة",
    svg: (p) => [[96, p.accent, 10, 1], [122, p.fg, 7, 0.8], [148, p.fg, 5, 0.55]].map(([b, c, w, o]) =>
      `<polyline points="${pts([[28, b], [64, b - 50], [100, b - 14], [136, b - 50], [172, b]])}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linejoin="miter" stroke-miterlimit="8" opacity="${o}"/>`).join(""),
  },

  // ---------- 4. The luxury monogram ----------
  {
    n: 13, name: "التشابك", idea: "M وW متشابكين: مونوغرام على طريقة بيوت الأزياء",
    svg: (p) => `<polyline points="44,152 44,50 100,114 156,50 156,152" fill="none" stroke="${p.fg}" stroke-width="9" stroke-linejoin="miter" stroke-miterlimit="10"/>
      <polyline points="44,152 100,88 156,152" fill="none" stroke="${p.accent}" stroke-width="9" stroke-linejoin="miter" stroke-miterlimit="10"/>`,
  },
  {
    n: 14, name: "الختم", idea: "ختم دائري بالاسمين، زي ختم الشمع",
    svg: (p) => {
      const top = uid("t14"), bot = uid("b14");
      return `<defs><path id="${top}" d="M27,100 A73,73 0 0 1 173,100"/><path id="${bot}" d="M17,100 A83,83 0 0 0 183,100"/></defs>
        <circle cx="100" cy="100" r="92" ${stroke(p.accent, 2.2)}/>
        <circle cx="100" cy="100" r="62" ${stroke(p.accent, 1.2, 'opacity=".7"')}/>
        <text font-family="Marcellus" font-size="15" letter-spacing="4.5" fill="${p.fg}"><textPath href="#${top}" startOffset="50%" text-anchor="middle">MASTRIX MEDIA</textPath></text>
        <text font-family="Amiri" font-weight="700" font-size="17" fill="${p.fg}"><textPath href="#${bot}" startOffset="50%" text-anchor="middle">ماستريكس ميديا</textPath></text>
        <circle cx="23" cy="100" r="3" fill="${p.accent}"/><circle cx="177" cy="100" r="3" fill="${p.accent}"/>
        <text x="100" y="128" text-anchor="middle" font-family="Marcellus" font-size="80" fill="${p.fg}">M</text>`;
    },
  },
  {
    n: 15, name: "الديدوني", idea: "M بخط ديدوني داخل إطار، ستايل مجلات الفخامة",
    svg: (p) => `<rect x="40" y="24" width="120" height="152" ${stroke(p.accent, 2)}/>
      <rect x="47" y="31" width="106" height="138" ${stroke(p.accent, 0.9, 'opacity=".6"')}/>
      <text x="100" y="141" text-anchor="middle" font-family="Bodoni Moda" font-weight="700" font-size="104" fill="${p.fg}">M</text>`,
  },
  {
    n: 16, name: "البؤرة", idea: "M بنقطة تركيز نحاسية بالنص: إحنا منركّز",
    svg: (p) => `<polyline points="40,162 40,46 100,110 160,46 160,162" ${stroke(p.fg, 16)}/>
      <circle cx="100" cy="112" r="17" fill="${p.accent}" stroke="${p.bg}" stroke-width="6"/>`,
  },

  // ---------- 5. The letter ----------
  {
    n: 17, name: "الإعجام", idea: "«ماستريكس» بالعربي، ونقاط الحروف نحاسية: النقطة هي الزبون",
    wide: true, // viewBox and paths come from logos/assets/ijam.svg (scripts/ijam_svg.py)
    svg: (p) => window.IJAM.inner.replace('class="skel"', `fill="${p.fg}"`).replace('class="dots"', `fill="${p.accent}"`),
  },
  {
    n: 18, name: "التقاطع", idea: "MASTRIX، والـX نقطة تقاطع: هون بيصير التحويل",
    svg: (p) => xMark(p, 18),
  },
  {
    n: 19, name: "المسارين", idea: "X من مسارين بيلتقوا: الإعلان والزبون",
    svg: (p) => `<path d="M48,44 C120,60 80,140 152,156" ${stroke(p.fg, 14)}/>
      <path d="M152,44 C80,60 120,140 48,156" ${stroke(p.bg, 28)}/>
      <path d="M152,44 C80,60 120,140 48,156" ${stroke(p.accent, 14)}/>`,
  },
  {
    n: 20, name: "نقطة آخر السطر", idea: "«M.» حرف ونقطة: الكلام خلص، النتيجة حكت",
    svg: (p) => `<path d="M28,160 V72 Q28,48 48,64 L90,104 L132,64 Q152,48 152,72 V160" ${stroke(p.fg, 17)}/>
      <circle cx="178" cy="152" r="12" fill="${p.accent}"/>`,
  },
];

function xMark(p, w) {
  const gap = w * 0.33;
  return `<line x1="50" y1="50" x2="150" y2="150" ${stroke(p.fg, w)}/>
    <line x1="150" y1="50" x2="50" y2="150" ${stroke(p.fg, w)}/>
    <circle cx="100" cy="100" r="${w * 0.95}" fill="${p.accent}" stroke="${p.bg}" stroke-width="${gap}"/>`;
}
window.xMark = xMark;

window.TERRITORIES = [
  { title: "المصفوفة", line: "كل نقطة شخص من جمهورك. بيكمّل فكرة الإعلان مباشرة", from: 1 },
  { title: "المحادثة", line: "شغلكم بيخلص بمحادثة واتساب، فخلّي اللوغو يحكيها", from: 5 },
  { title: "النمو", line: "النتيجة بالأرقام: خط، أعمدة، صفقة، قمّة", from: 9 },
  { title: "الختم الفاخر", line: "لغة بيوت الأزياء والبنوك الخاصة", from: 13 },
  { title: "الحرف", line: "الاسم نفسه هو اللوغو", from: 17 },
];
