// 读取 GLB 文件并打印模型层级大纲，结果同时保存为 txt 到模型目录
// 用法: node scripts/printModelTree.mjs

import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname, basename, extname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const glbPath = resolve(__dirname, "../public/model/glb/server_room.glb");
const glbDir = dirname(glbPath);
const glbBaseName = basename(glbPath, extname(glbPath)); // e.g. "server_room"
const txtPath = resolve(glbDir, `${glbBaseName}.txt`);

// ========== 收集输出的辅助 ==========
const outputLines = [];
function log(line = "") {
  outputLines.push(line);
  console.log(line);
}

// ========== 读取 GLB 二进制 ==========
const buffer = readFileSync(glbPath);
const dataView = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);

// GLB Header: magic(4) + version(4) + length(4) = 12 bytes
const magic = dataView.getUint32(0, true); // little-endian
if (magic !== 0x46546C67) {
  log("❌ 不是有效的 GLB 文件 (magic number 不匹配)");
  process.exit(1);
}
const version = dataView.getUint32(4, true);
const totalLength = dataView.getUint32(8, true);

log(`📦 GLB v${version}, 总大小: ${(totalLength / 1024).toFixed(1)} KB`);
log();

// ========== 解析 Chunks ==========
let offset = 12;
let jsonData = null;

while (offset < totalLength) {
  const chunkLength = dataView.getUint32(offset, true);
  const chunkType = dataView.getUint32(offset + 4, true);
  offset += 8;

  if (chunkType === 0x4E4F534A) {
    // JSON chunk
    const jsonBytes = buffer.subarray(offset, offset + chunkLength);
    jsonData = JSON.parse(new TextDecoder().decode(jsonBytes));
  }
  // BIN chunk (0x004E4942) — 跳过，只关心结构

  offset += chunkLength;
}

if (!jsonData) {
  log("❌ 未找到 JSON chunk");
  process.exit(1);
}

// ========== 构建索引 ==========
const meshIndex = {};   // meshIdx -> name
const nodeIndex = {};   // nodeIdx -> { name, meshName, children }

if (jsonData.meshes) {
  jsonData.meshes.forEach((m, i) => {
    meshIndex[i] = m.name || `mesh_${i}`;
  });
}

if (jsonData.nodes) {
  jsonData.nodes.forEach((n, i) => {
    nodeIndex[i] = {
      name: n.name || `node_${i}`,
      meshIdx: n.mesh,
      meshName: n.mesh !== undefined ? meshIndex[n.mesh] || `mesh_${n.mesh}` : null,
      children: n.children || [],
    };
  });
}

// ========== 打印层级树 ==========
const rootNodes = jsonData.scenes?.[jsonData.scene ?? 0]?.nodes ?? [];

function printTree(nodeIdx, indent = "", isLast = true) {
  const node = nodeIndex[nodeIdx];
  if (!node) return;

  const prefix = indent + (isLast ? "└── " : "├── ");
  const childIndent = indent + (isLast ? "    " : "│   ");

  // 节点名 + 类型标记
  let label = node.name;
  if (node.meshName) {
    label += ` → 🧊 [${node.meshName}]`;
  } else if (node.children.length > 0) {
    label += ` → 📁 (Group: ${node.children.length} children)`;
  } else {
    label += ` → ⚪ (Empty)`;
  }

  log(prefix + label);

  node.children.forEach((childIdx, i) => {
    printTree(childIdx, childIndent, i === node.children.length - 1);
  });
}

log("🏗️  模型层级大纲:");
log();
log(`   场景包含 ${rootNodes.length} 个根节点`);
log();

rootNodes.forEach((rootIdx, i) => {
  printTree(rootIdx, "", i === rootNodes.length - 1);
});

// ========== 统计 ==========
let totalMeshes = 0;
let totalTriangles = 0;
if (jsonData.meshes) {
  totalMeshes = jsonData.meshes.length;
  jsonData.meshes.forEach((m) => {
    m.primitives.forEach((p) => {
      if (jsonData.accessors?.[p.indices ?? -1]) {
        totalTriangles += jsonData.accessors[p.indices].count / 3;
      }
    });
  });
}

log();
log(`📊 统计:`);
log(`   节点总数: ${jsonData.nodes?.length ?? 0}`);
log(`   Mesh 数: ${totalMeshes}`);
log(`   三角面数: ${Math.round(totalTriangles).toLocaleString()}`);
if (jsonData.materials) {
  log(`   材质数: ${jsonData.materials.length}`);
  jsonData.materials.forEach((mat, i) => {
    log(`      [${i}] ${mat.name || "未命名"}`);
  });
} else {
  log(`   材质数: 0 (无材质，白模)`);
}

// ========== 保存到 txt ==========
writeFileSync(txtPath, outputLines.join("\n"), "utf-8");
log();
log(`✅ 结果已保存至: ${txtPath}`);
