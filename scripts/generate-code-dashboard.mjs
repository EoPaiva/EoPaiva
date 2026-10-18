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
const README_FILE = path.join(ROOT_DIR, "README.md");

const STABLE_DASHBOARD_FILE = "github-code-dashboard.svg";
const STABLE_OUTPUT_FILE = path.join(ASSETS_DIR, STABLE_DASHBOARD_FILE);

const START_MARKER = "<!-- CODE_DASHBOARD:START -->";
const END_MARKER = "<!-- CODE_DASHBOARD:END -->";

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

function timestampForFileName() {
  return new Date()
    .toISOString()
    .replaceAll("-", "")
    .replaceAll(":", "")
    .replaceAll(".", "")
    .replace("T", "")
    .replace("Z", "")
    .slice(0, 14);
}

function dashboardBlock(fileName) {
  return `${START_MARKER}
<p align="center">
  <img width="100%" src="./assets/${fileName}" alt="Painel automático de código em produção — linhas, palavras, repositórios e linguagens" />
</p>
${END_MARKER}`;
}

function updateReadmeDashboardReference(fileName) {
  if (!fs.existsSync(README_FILE)) return;

  let readme = fs.readFileSync(README_FILE, "utf8");
  const nextBlock = dashboardBlock(fileName);
  const markerRegex = new RegExp(`${START_MARKER}[\\s\\S]*?${END_MARKER}`, "m");

  if (markerRegex.test(readme)) {
    readme = readme.replace(markerRegex, nextBlock);
    fs.writeFileSync(README_FILE, readme, "utf8");
    return;
  }

  const section = `
---

## 🛰️ \`codigo_em_producao = {\`

${nextBlock}

<p align="center">
  <sub>Painel gerado automaticamente com base nos repositórios públicos do GitHub, contabilizando linhas, palavras, arquivos analisados e principais tecnologias em uso.</sub>
</p>

\`}\`

`;

  const telemetryTitle = "## 📊 `telemetria_do_github`";

  if (readme.includes(telemetryTitle)) {
    readme = readme.replace(telemetryTitle, `${section}${telemetryTitle}`);
  } else {
    readme += section;
  }

  fs.writeFileSync(README_FILE, readme, "utf8");
}

function cleanOldGeneratedDashboards(currentFileName) {
  if (!fs.existsSync(ASSETS_DIR)) return;

  for (const file of fs.readdirSync(ASSETS_DIR)) {
    const isGeneratedDashboard = /^github-code-dashboard-\d{14}\.svg$/.test(file);

    if (isGeneratedDashboard && file !== currentFileName) {
      fs.rmSync(path.join(ASSETS_DIR, file), { force: true });
    }
  }
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

function isIgnoredFile(fileName) {
  if (IGNORED_FILES.has(fileName)) return true;
  if (/^github-code-dashboard(?:-\d{14})?\.svg$/.test(fileName)) return true;
  return false;
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

      if (entry.isFile() && !isIgnoredFile(entry.name)) {
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

const FONT_DIR = path.join(ASSETS_DIR, "fonts");

function embeddedFonts() {
  const faces = [
    ["T", "inter-display-thin.woff2"],
    ["M", "inter-medium.woff2"],
    ["R", "inter-regular.woff2"],
  ];

  return faces
    .filter(([, file]) => fs.existsSync(path.join(FONT_DIR, file)))
    .map(([family, file]) => {
      const data = fs.readFileSync(path.join(FONT_DIR, file)).toString("base64");
      return `@font-face{font-family:'${family}';src:url(data:font/woff2;base64,${data}) format('woff2');}`;
    })
    .join("\n");
}

function languageShares(languageLines) {
  const entries = [...languageLines.entries()]
    .filter(([language]) => !["JSON", "YAML", "XML", "SVG"].includes(language))
    .sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, lines]) => sum + lines, 0);
  if (!total) return [];

  const top = entries.slice(0, 5).map(([language, lines]) => ({ language, share: lines / total }));
  const rest = 1 - top.reduce((sum, item) => sum + item.share, 0);
  if (rest > 0.005) top.push({ language: "Outras", share: rest });
  return top;
}

function generateSvg(stats) {
  const { totalLines, totalWords, analyzedRepos, analyzedFiles, technologies, languageLines } = stats;

  const repositoryLabel = INCLUDE_PRIVATE ? "repositórios analisados" : "repositórios públicos";
  const updatedAt = nowInBrazil();
  const sans = "'Helvetica Neue',Helvetica,Arial,sans-serif";
  const shades = ["#ffffff", "#c4c4c4", "#8f8f8f", "#5e5e5e", "#3a3a3a", "#242424"];

  const metrics = [
    [formatNumber(totalLines), "linhas analisadas"],
    [formatNumber(totalWords), "palavras mapeadas"],
    [formatNumber(analyzedRepos), repositoryLabel],
  ];

  const metricBlocks = metrics
    .map(
      ([value, label], index) => `
  <g class="rise" style="animation-delay:${0.15 + index * 0.15}s">
    <text x="${64 + index * 400}" y="200" font-family="T,${sans}" font-size="84" letter-spacing="-3" fill="#fff">${escapeXml(value)}</text>
    <text x="${66 + index * 400}" y="236" font-family="R,${sans}" font-size="15" fill="#8c8c8c">${escapeXml(label)}</text>
  </g>`
    )
    .join("");

  const shares = languageShares(languageLines);
  let languageBlock;

  if (shares.length) {
    let cursor = 64;
    const barWidth = 1152;
    const bars = shares
      .map(({ share }, index) => {
        const width = Math.max(share * barWidth - 4, 2);
        const rect = `<rect class="grow" style="animation-delay:${0.5 + index * 0.12}s" x="${cursor.toFixed(1)}" y="318" width="${width.toFixed(1)}" height="10" rx="2" fill="${shades[index]}"/>`;
        cursor += share * barWidth;
        return rect;
      })
      .join("");

    const legend = shares
      .map(({ language, share }, index) => {
        const x = 64 + index * 192;
        return `<circle cx="${x + 4}" cy="368" r="4" fill="${shades[index]}" stroke="#3a3a3a"/>
    <text x="${x + 18}" y="373" font-family="R,${sans}" font-size="14" fill="#d4d4d4">${escapeXml(language)}</text>
    <text x="${x + 18}" y="396" font-family="M,${sans}" font-size="11" letter-spacing="2" fill="#5c5c5c">${(share * 100).toFixed(1).replace(".", ",")}%</text>`;
      })
      .join("\n    ");

    languageBlock = `${bars}
    ${legend}`;
  } else {
    languageBlock = `<rect x="64" y="318" width="1152" height="10" rx="2" fill="#1d1d1d"/>
    <text x="64" y="373" font-family="R,${sans}" font-size="16" fill="#d4d4d4">${escapeXml(technologies)}</text>`;
  }

  return `
<svg width="1280" height="500" viewBox="0 0 1280 500" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Código em produção — painel automático do GitHub</title>
  <desc id="desc">${escapeXml(formatNumber(totalLines))} linhas, ${escapeXml(formatNumber(totalWords))} palavras e ${escapeXml(formatNumber(analyzedRepos))} ${escapeXml(repositoryLabel)}. Principais linguagens: ${escapeXml(technologies)}.</desc>
  <style>
${embeddedFonts()}
@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes pulse{from{transform:scale(1);opacity:.8}to{transform:scale(3);opacity:0}}
.rise{animation:rise 1.1s cubic-bezier(.16,1,.3,1) both}
.grow{transform-box:fill-box;transform-origin:left center;animation:grow 1.4s cubic-bezier(.65,0,.35,1) both}
.pl{transform-box:fill-box;transform-origin:center;animation:pulse 2s cubic-bezier(.2,.6,.3,1) infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
  </style>

  <rect width="1280" height="500" rx="22" fill="#050505"/>
  <rect x=".5" y=".5" width="1279" height="499" rx="21.5" fill="none" stroke="#1d1d1d"/>

  <circle class="pl" cx="70" cy="70" r="3.5" fill="#fff"/>
  <circle cx="70" cy="70" r="3.5" fill="#fff"/>
  <text x="86" y="74.5" font-family="M,${sans}" font-size="11.5" letter-spacing="3.4" fill="#cfcfcf">AO VIVO · ATUALIZA A CADA 6 HORAS</text>
  <text x="1216" y="74.5" text-anchor="end" font-family="M,${sans}" font-size="11.5" letter-spacing="3.4" fill="#5c5c5c">SYNC ${escapeXml(updatedAt)}</text>
  <rect x="64" y="102" width="1152" height="1" fill="#1d1d1d"/>
  <rect x="440" y="134" width="1" height="110" fill="#1d1d1d"/>
  <rect x="840" y="134" width="1" height="110" fill="#1d1d1d"/>
${metricBlocks}

  <text x="64" y="294" font-family="M,${sans}" font-size="11.5" letter-spacing="3.4" fill="#5c5c5c">LINGUAGENS POR LINHA DE CÓDIGO</text>
  <text x="1216" y="294" text-anchor="end" font-family="M,${sans}" font-size="11.5" letter-spacing="3.4" fill="#5c5c5c">${escapeXml(formatNumber(analyzedFiles))} ARQUIVOS</text>
  <g>
    ${languageBlock}
  </g>

  <rect x="64" y="432" width="1152" height="1" fill="#1d1d1d"/>
  <text x="64" y="466" font-family="M,${sans}" font-size="11" letter-spacing="3" fill="#5c5c5c">GERADO POR GITHUB ACTIONS A PARTIR DOS REPOSITÓRIOS PÚBLICOS</text>
  <text x="1216" y="466" text-anchor="end" font-family="M,${sans}" font-size="11" letter-spacing="3" fill="#5c5c5c">BUILD · AUTOMATE · SCALE</text>
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

  const timestampedFileName = `github-code-dashboard-${timestampForFileName()}.svg`;
  const timestampedOutputFile = path.join(ASSETS_DIR, timestampedFileName);

  fs.writeFileSync(STABLE_OUTPUT_FILE, svg, "utf8");
  fs.writeFileSync(timestampedOutputFile, svg, "utf8");

  updateReadmeDashboardReference(timestampedFileName);
  cleanOldGeneratedDashboards(timestampedFileName);

  fs.rmSync(TEMP_DIR, { recursive: true, force: true });

  console.log(
    `Código em produção atualizado: ${formatNumber(totalLines)} linhas, ${formatNumber(totalWords)} palavras, ${formatNumber(analyzedRepos)} repositórios.`
  );
  console.log(`README atualizado para usar: assets/${timestampedFileName}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
