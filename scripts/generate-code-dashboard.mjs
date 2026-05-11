import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const USERNAME = process.env.GITHUB_USERNAME || "EoPaiva";
const GH_STATS_TOKEN = process.env.GH_STATS_TOKEN || "";
const INCLUDE_PRIVATE = process.env.INCLUDE_PRIVATE === "true";
const INCLUDE_FORKS = process.env.INCLUDE_FORKS === "true";
const INCLUDE_ARCHIVED = process.env.INCLUDE_ARCHIVED === "true";

const ROOT_DIR = process.cwd();
const TEMP_DIR = path.join(ROOT_DIR, ".tmp-code-dashboard");
const ASSETS_DIR = path.join(ROOT_DIR, "assets");
const OUTPUT_FILE = path.join(ASSETS_DIR, "github-code-dashboard.svg");

const IGNORED_DIRS = new Set([
  ".git",
  ".github",
  "node_modules",
  ".next",
  "dist",
  "build",
  "coverage",
  ".vercel",
  "out",
  ".turbo",
  ".cache",
  "vendor",
  "venv",
  ".venv",
  "target",
  "bin",
  "obj",
  "public",
  "static",
]);

const IGNORED_FILES = new Set([
  "package-lock.json",
  "yarn.lock",
  "pnpm-lock.yaml",
  "bun.lockb",
  "composer.lock",
  "Cargo.lock",
]);

const EXTENSION_TO_LANGUAGE = new Map([
  [".ts", "TypeScript"],
  [".tsx", "TypeScript"],
  [".mts", "TypeScript"],
  [".cts", "TypeScript"],
  [".js", "JavaScript"],
  [".jsx", "JavaScript"],
  [".mjs", "JavaScript"],
  [".cjs", "JavaScript"],
  [".css", "CSS"],
  [".scss", "CSS"],
  [".sass", "CSS"],
  [".html", "HTML"],
  [".htm", "HTML"],
  [".md", "Markdown"],
  [".mdx", "Markdown"],
  [".json", "JSON"],
  [".py", "Python"],
  [".php", "PHP"],
  [".java", "Java"],
  [".go", "Go"],
  [".rs", "Rust"],
  [".c", "C"],
  [".h", "C"],
  [".cpp", "C++"],
  [".hpp", "C++"],
  [".cs", "C#"],
  [".sql", "SQL"],
  [".yml", "YAML"],
  [".yaml", "YAML"],
  [".xml", "XML"],
  [".svg", "SVG"],
  [".sh", "Shell"],
  [".bash", "Shell"],
  [".ps1", "PowerShell"],
]);

function run(command, args, options = {}) {
  execFileSync(command, args, {
    stdio: "ignore",
    ...options,
  });
}

function formatNumber(value) {
  return new Intl.NumberFormat("pt-BR").format(value);
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function nowInBrazil() {
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

async function githubRequest(url) {
  const headers = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "mpaiva-github-code-dashboard",
  };

  if (GH_STATS_TOKEN) {
    headers.Authorization = `Bearer ${GH_STATS_TOKEN}`;
  }

  const response = await fetch(url, { headers });

  if (!response.ok) {
    throw new Error(`GitHub API: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

async function getRepositories() {
  const repositories = [];

  for (let page = 1; page <= 10; page++) {
    const url = INCLUDE_PRIVATE
      ? `https://api.github.com/user/repos?visibility=all&affiliation=owner&sort=updated&per_page=100&page=${page}`
      : `https://api.github.com/users/${USERNAME}/repos?type=owner&sort=updated&per_page=100&page=${page}`;

    const data = await githubRequest(url);
    if (!Array.isArray(data) || data.length === 0) break;

    repositories.push(...data);
  }

  return repositories.filter((repo) => {
    if (!INCLUDE_FORKS && repo.fork) return false;
    if (!INCLUDE_ARCHIVED && repo.archived) return false;
    if (!INCLUDE_PRIVATE && repo.private) return false;
    return true;
  });
}

function prepareDirectories() {
  fs.rmSync(TEMP_DIR, { recursive: true, force: true });
  fs.mkdirSync(TEMP_DIR, { recursive: true });
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

function safeFolderName(value) {
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "_");
}

function authenticatedCloneUrl(repo) {
  if (!GH_STATS_TOKEN || !repo.clone_url.startsWith("https://")) {
    return repo.clone_url;
  }

  return repo.clone_url.replace(
    "https://",
    `https://x-access-token:${encodeURIComponent(GH_STATS_TOKEN)}@`
  );
}

function getAllFiles(directory) {
  const files = [];

  function walk(currentDirectory) {
    const entries = fs.readdirSync(currentDirectory, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentDirectory, entry.name);

      if (entry.isDirectory()) {
        if (!IGNORED_DIRS.has(entry.name)) {
          walk(fullPath);
        }
        continue;
      }

      if (entry.isFile() && !IGNORED_FILES.has(entry.name)) {
        files.push(fullPath);
      }
    }
  }

  walk(directory);
  return files;
}

function countFile(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  const language = EXTENSION_TO_LANGUAGE.get(extension);

  if (!language) return null;

  let content = "";

  try {
    const stats = fs.statSync(filePath);
    if (stats.size > 1_500_000) return null;
    content = fs.readFileSync(filePath, "utf8");
  } catch {
    return null;
  }

  const normalized = content.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = normalized.length === 0 ? 0 : normalized.split("\n").length;
  const words = normalized.match(/[\p{L}\p{N}_]+/gu)?.length || 0;

  return { language, lines, words };
}

function topTechnologies(languageLines) {
  const preferredOrder = [
    "TypeScript",
    "JavaScript",
    "CSS",
    "Markdown",
    "HTML",
    "Python",
    "PHP",
    "SQL",
  ];

  const sorted = [...languageLines.entries()]
    .filter(([language]) => !["JSON", "YAML", "XML", "SVG"].includes(language))
    .sort((a, b) => b[1] - a[1])
    .map(([language]) => language);

  const ordered = [
    ...preferredOrder.filter((language) => sorted.includes(language)),
    ...sorted.filter((language) => !preferredOrder.includes(language)),
  ];

  return ordered.slice(0, 4).join(" • ") || "TypeScript • JavaScript • CSS • Markdown";
}

function compactSparkline(values, x, y, width, height) {
  if (!values.length) return "";

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / Math.max(values.length - 1, 1);

  return values
    .map((value, index) => {
      const pointX = x + index * step;
      const pointY = y + height - ((value - min) / range) * height;
      return `${index === 0 ? "M" : "L"}${pointX.toFixed(1)} ${pointY.toFixed(1)}`;
    })
    .join(" ");
}

function generateSvg(stats) {
  const {
    totalLines,
    totalWords,
    analyzedRepos,
    analyzedFiles,
    technologies,
    languageLines,
  } = stats;

  const languageValues = [...languageLines.values()].sort((a, b) => b - a).slice(0, 18);
  const sparkline = compactSparkline(languageValues.length ? languageValues : [2, 6, 4, 9, 7, 12, 8], 90, 360, 820, 42);

  const repositoryLabel = INCLUDE_PRIVATE ? "repositórios analisados" : "repositórios públicos";
  const updatedAt = nowInBrazil();

  return `
<svg width="1200" height="620" viewBox="0 0 1200 620" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Código em produção — painel automático do GitHub</title>
  <desc id="desc">Painel com linhas analisadas, palavras, repositórios públicos, arquivos e principais tecnologias.</desc>

  <defs>
    <radialGradient id="mainGlow" cx="50%" cy="0%" r="95%">
      <stop offset="0%" stop-color="#19ff99" stop-opacity="0.22"/>
      <stop offset="42%" stop-color="#07110d" stop-opacity="0.62"/>
      <stop offset="100%" stop-color="#020403" stop-opacity="1"/>
    </radialGradient>
    <linearGradient id="greenBorder" x1="0" y1="0" x2="1200" y2="620">
      <stop stop-color="#29ff8f" stop-opacity="0.9"/>
      <stop offset="0.45" stop-color="#29ff8f" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#29ff8f" stop-opacity="0.65"/>
    </linearGradient>
    <filter id="glow" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feColorMatrix in="blur" type="matrix" values="0 0 0 0 0.10 0 0 0 0 1 0 0 0 0 0.52 0 0 0 0.68 0"/>
      <feBlend in="SourceGraphic"/>
    </filter>
    <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse">
      <path d="M 34 0 L 0 0 0 34" fill="none" stroke="#ffffff" stroke-opacity="0.035" stroke-width="1"/>
      <circle cx="2" cy="2" r="1" fill="#29ff8f" opacity="0.12"/>
    </pattern>
  </defs>

  <rect width="1200" height="620" rx="34" fill="#020403"/>
  <rect width="1200" height="620" rx="34" fill="url(#mainGlow)"/>
  <rect width="1200" height="620" fill="url(#grid)" opacity="0.95"/>
  <rect x="2" y="2" width="1196" height="616" rx="32" stroke="url(#greenBorder)" stroke-width="2"/>

  <path d="M72 85H858L880 63H1126" stroke="#29ff8f" stroke-opacity="0.18"/>
  <path d="M78 493H1118" stroke="#29ff8f" stroke-opacity="0.16"/>
  <path d="M80 178H1120" stroke="#29ff8f" stroke-opacity="0.18"/>

  <text x="72" y="70" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="25" letter-spacing="8">M PAIVA _</text>
  <text x="72" y="108" fill="#d5ddd8" font-family="Consolas, 'Courier New', monospace" font-size="17" opacity="0.76">Arquitetura de IA • Desenvolvimento Web • Automação &amp; Gestão Estratégica</text>
  <text x="970" y="92" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="14" opacity="0.78">MP://SYSTEM</text>

  <text x="72" y="164" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="20">● / Code_Production</text>
  <text x="72" y="235" fill="#f2f5f2" font-family="Consolas, 'Courier New', monospace" font-size="62" font-weight="800" letter-spacing="3">CÓDIGO EM PRODUÇÃO</text>
  <text x="72" y="278" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="23">dashboard automático do GitHub</text>

  <g>
    <rect x="72" y="324" width="502" height="124" rx="18" fill="#05100b" fill-opacity="0.76" stroke="#29ff8f" stroke-opacity="0.72"/>
    <text x="102" y="374" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="44" font-weight="800">${escapeXml(formatNumber(totalLines))}</text>
    <text x="104" y="414" fill="#d5ddd8" font-family="Consolas, 'Courier New', monospace" font-size="21">linhas analisadas</text>
    <text x="426" y="352" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="13" opacity="0.75">// LINES.SRC ■</text>
  </g>

  <g>
    <rect x="626" y="324" width="502" height="124" rx="18" fill="#05100b" fill-opacity="0.62" stroke="#ffffff" stroke-opacity="0.22"/>
    <text x="656" y="374" fill="#f2f5f2" font-family="Consolas, 'Courier New', monospace" font-size="44" font-weight="800">${escapeXml(formatNumber(totalWords))}</text>
    <text x="658" y="414" fill="#d5ddd8" font-family="Consolas, 'Courier New', monospace" font-size="21">palavras mapeadas</text>
    <text x="978" y="352" fill="#d5ddd8" font-family="Consolas, 'Courier New', monospace" font-size="13" opacity="0.68">// WORDS.MAP ■</text>
  </g>

  <g>
    <rect x="72" y="474" width="502" height="94" rx="18" fill="#05100b" fill-opacity="0.62" stroke="#ffffff" stroke-opacity="0.18"/>
    <text x="102" y="527" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="36" font-weight="800">${escapeXml(formatNumber(analyzedRepos))}</text>
    <text x="185" y="527" fill="#d5ddd8" font-family="Consolas, 'Courier New', monospace" font-size="20">${escapeXml(repositoryLabel)}</text>
    <text x="104" y="552" fill="#71847b" font-family="Consolas, 'Courier New', monospace" font-size="15">${escapeXml(formatNumber(analyzedFiles))} arquivos analisados • atualizado automaticamente</text>
  </g>

  <g>
    <rect x="626" y="474" width="502" height="94" rx="18" fill="#05100b" fill-opacity="0.76" stroke="#29ff8f" stroke-opacity="0.55"/>
    <text x="656" y="515" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="18" font-weight="800">STACK PRINCIPAL</text>
    <text x="656" y="548" fill="#f2f5f2" font-family="Consolas, 'Courier New', monospace" font-size="22" font-weight="700">${escapeXml(technologies)}</text>
  </g>

  <path d="${sparkline}" stroke="#29ff8f" stroke-opacity="0.68" stroke-width="2" fill="none"/>
  <circle cx="910" cy="${languageValues.length ? 381 : 360}" r="4" fill="#29ff8f" filter="url(#glow)"/>

  <text x="74" y="598" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="14" opacity="0.75">MP://DEV_MODE</text>
  <text x="446" y="598" fill="#29ff8f" font-family="Consolas, 'Courier New', monospace" font-size="14" letter-spacing="8" opacity="0.65">BUILD · AUTOMATE · SCALE</text>
  <text x="934" y="598" fill="#71847b" font-family="Consolas, 'Courier New', monospace" font-size="14">última sync: ${escapeXml(updatedAt)}</text>

  <g filter="url(#glow)">
    <circle cx="1062" cy="160" r="4" fill="#29ff8f"/>
    <circle cx="1102" cy="438" r="5" fill="#29ff8f"/>
    <circle cx="968" cy="292" r="3" fill="#29ff8f"/>
  </g>
</svg>
`.trim();
}

async function main() {
  prepareDirectories();

  const repositories = await getRepositories();

  let totalLines = 0;
  let totalWords = 0;
  let analyzedRepos = 0;
  let analyzedFiles = 0;
  const languageLines = new Map();

  for (const repo of repositories) {
    const folder = path.join(TEMP_DIR, safeFolderName(`${repo.owner?.login || USERNAME}_${repo.name}`));

    try {
      run("git", ["clone", "--depth=1", "--single-branch", authenticatedCloneUrl(repo), folder]);

      const files = getAllFiles(folder);
      let repoCounted = false;

      for (const file of files) {
        const result = countFile(file);
        if (!result) continue;

        repoCounted = true;
        analyzedFiles += 1;
        totalLines += result.lines;
        totalWords += result.words;
        languageLines.set(result.language, (languageLines.get(result.language) || 0) + result.lines);
      }

      if (repoCounted) analyzedRepos += 1;
    } catch {
      continue;
    }
  }

  const svg = generateSvg({
    totalLines,
    totalWords,
    analyzedRepos,
    analyzedFiles,
    technologies: topTechnologies(languageLines),
    languageLines,
  });

  fs.writeFileSync(OUTPUT_FILE, svg, "utf8");

  fs.rmSync(TEMP_DIR, { recursive: true, force: true });

  console.log(`Código em produção atualizado: ${formatNumber(totalLines)} linhas, ${formatNumber(totalWords)} palavras, ${formatNumber(analyzedRepos)} repositórios.`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
