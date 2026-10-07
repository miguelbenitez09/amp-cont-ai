/* Checks that the three browser dictionaries expose the same key paths. */
const fs = require("fs");
const vm = require("vm");
const files = { es: "src/serving/static/js/i18n/es.js", en: "src/serving/static/js/i18n/en.js", pt: "src/serving/static/js/i18n/pt.js" };
const context = { window: {} };
vm.createContext(context);
for (const file of Object.values(files)) vm.runInContext(fs.readFileSync(file, "utf8"), context, { filename: file });
const dictionaries = { es: context.window.I18N_ES, en: context.window.I18N_EN, pt: context.window.I18N_PT };
const groups = ["nav", "cot", "customs", "forecast", "benchmark", "simulation", "data_platform", "security", "telemetry", "common", "footer"];
for (const dictionary of Object.values(dictionaries)) {
  for (const [flatKey, value] of Object.entries(dictionary._coverage || {})) {
    const group = groups.find(prefix => flatKey.startsWith(`${prefix}_`));
    if (!group) continue;
    dictionary[group] = dictionary[group] || {};
    const key = flatKey.slice(group.length + 1);
    if (!(key in dictionary[group])) dictionary[group][key] = value;
  }
  delete dictionary._coverage;
}
function paths(value, prefix = "", output = new Set()) {
  for (const [key, child] of Object.entries(value || {})) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (child && typeof child === "object" && !Array.isArray(child)) paths(child, path, output);
    else output.add(path);
  }
  return output;
}
const all = new Set([...Object.values(dictionaries)].flatMap(dictionary => [...paths(dictionary)]));
const missing = {};
for (const [lang, dictionary] of Object.entries(dictionaries)) missing[lang] = [...all].filter(key => !paths(dictionary).has(key));
if (Object.values(missing).some(items => items.length)) {
  console.error(JSON.stringify(missing, null, 2));
  process.exit(1);
}
console.log(JSON.stringify({ languages: Object.keys(dictionaries), key_count: all.size, complete: true }));
