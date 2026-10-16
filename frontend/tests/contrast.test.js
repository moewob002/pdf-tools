// WCAG AA contrast for the design tokens in src/style.css, in both themes.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/style.css", import.meta.url), "utf8");

function block(selector) {
  const start = css.indexOf(selector + " {");
  assert.ok(start >= 0, `missing ${selector}`);
  const body = css.slice(start, css.indexOf("}", start));
  const vars = {};
  for (const [, name, value] of body.matchAll(/--([\w-]+):\s*([^;]+);/g)) vars[name] = value.trim();
  return vars;
}

const light = block(":root");
const themes = { light, dark: { ...light, ...block(':root[data-theme="dark"]') } };

const rgb = (vars, name) => {
  const value = vars[`c-${name}`];
  assert.ok(value, `token --c-${name} missing`);
  return value.split(/\s+/).map(Number);
};
const lum = (c) => {
  const [r, g, b] = c.map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};
const blend = (fg, bg, alpha) => fg.map((c, i) => Math.round(c * alpha + bg[i] * (1 - alpha)));

const TEXT = ["fg", "muted", "primary-text", "secondary-text", "accent-text", "cyan-text", "success", "warning", "danger", "info"];
const SURFACES = ["bg", "surface", "surface-2"];

for (const [name, vars] of Object.entries(themes)) {
  const c = (token) => rgb(vars, token);
  const failures = [];
  const check = (label, a, b, min) => {
    const r = ratio(a, b);
    if (r < min) failures.push(`${label}: ${r.toFixed(2)} < ${min}`);
  };

  test(`${name} theme meets WCAG AA`, () => {
    for (const t of TEXT) for (const s of SURFACES) check(`${t} on ${s}`, c(t), c(s), 4.5);

    // Text on the brand gradient (primary buttons, active nav, step badges): both stops.
    for (const stop of ["primary", "secondary"]) check(`on-primary on ${stop}`, c("on-primary"), c(stop), 4.5);

    // Status messages: coloured text on their own 10% tint.
    for (const s of ["success", "warning", "danger", "info", "primary-text"]) {
      check(`${s} on ${s}/10 tint`, c(s), blend(c(s), c("surface"), 0.1), 4.5);
    }
    // Tool icon chips (graphics, 3:1).
    for (const t of ["primary-text", "secondary-text", "cyan-text", "accent-text"]) {
      check(`${t} icon on its chip`, c(t), blend(c(t), c("surface"), 0.1), 3);
    }
    // Component boundaries and focus indicator (3:1).
    for (const s of SURFACES) {
      check(`line-strong vs ${s}`, c("line-strong"), c(s), 3);
      check(`focus vs ${s}`, c("focus"), c(s), 3);
    }
    // Hero text sits over translucent colour blobs.
    const alpha = Number(vars["hero-blob-opacity"]);
    for (const base of ["bg", "surface"]) {
      for (const blob of ["primary", "secondary", "accent", "cyan"]) {
        const behind = blend(c(blob), c(base), alpha);
        check(`fg over ${blob} hero blob on ${base}`, c("fg"), behind, 4.5);
        check(`muted over ${blob} hero blob on ${base}`, c("muted"), behind, 4.5);
      }
    }

    assert.deepEqual(failures, []);
  });
}

test("the no-JS dark fallback matches the dark theme", () => {
  const fallback = block(":root:not([data-theme])");
  for (const [name, value] of Object.entries(fallback)) {
    assert.equal(value, themes.dark[name], `--${name} differs between fallback and dark theme`);
  }
});

