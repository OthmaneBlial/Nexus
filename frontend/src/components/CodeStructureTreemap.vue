<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import * as d3 from "d3";

import type { CodeUnit } from "@/types/udm";

const props = defineProps<{
  codeUnits: CodeUnit[];
}>();

const svgRef = ref<SVGSVGElement | null>(null);
const containerRef = ref<HTMLDivElement | null>(null);
let resizeObserver: ResizeObserver | null = null;

type TreeNode = {
  name: string;
  path: string;
  children?: TreeNode[];
  value?: number;
  complexity?: number;
};

const tooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  name: "",
  path: "",
  metrics: "",
});

const sizeMetric = ref<"loc" | "complexity">("loc");
const colorMetric = ref<"complexity" | "loc">("complexity");
const showLabels = ref(true);

const humanReadable = (metric: "loc" | "complexity") =>
  metric === "loc" ? "Lines of Code" : "Cyclomatic Complexity";

const legendLabel = computed(
  () => `Size · ${humanReadable(sizeMetric.value)}   |   Color · ${humanReadable(colorMetric.value)}`,
);

function positionTooltip(event: MouseEvent) {
  if (!containerRef.value) return;
  const bounds = containerRef.value.getBoundingClientRect();
  const offsetX = event.clientX - bounds.left + 14;
  const offsetY = event.clientY - bounds.top + 14;
  const maxX = Math.max(12, bounds.width - 224);
  const maxY = Math.max(12, bounds.height - 140);
  tooltip.x = Math.min(Math.max(12, offsetX), maxX);
  tooltip.y = Math.min(Math.max(12, offsetY), maxY);
}

function showTooltip(event: MouseEvent, node: d3.HierarchyRectangularNode<TreeNode>) {
  positionTooltip(event);
  tooltip.visible = true;
  tooltip.name = node.data.name;
  tooltip.path = node.data.path;
  const loc = node.data.value ?? 0;
  const complexity = node.data.complexity ?? 0;
  tooltip.metrics = `${loc} LOC · ${complexity.toFixed(1)} CC`;
}

function moveTooltip(event: MouseEvent) {
  if (!tooltip.visible) return;
  positionTooltip(event);
}

function hideTooltip() {
  tooltip.visible = false;
}

function buildHierarchy(units: CodeUnit[]): TreeNode {
  const root: TreeNode = { name: "root", path: ".", children: [] };

  for (const unit of units) {
    const parts = unit.path.split("/");
    let cursor = root;
    let prefix = "";

    for (const [index, part] of parts.entries()) {
      prefix = prefix ? `${prefix}/${part}` : part;
      if (!cursor.children) {
        cursor.children = [];
      }
      let child = cursor.children.find((node) => node.name === part);
      if (!child) {
        child = { name: part, path: prefix, children: [] };
        cursor.children.push(child);
      }
      if (index === parts.length - 1) {
        child.value = unit.metrics.loc ?? 0;
        child.complexity = unit.metrics.complexity ?? 0;
      }
      cursor = child;
    }
  }

  return root;
}

function metricValue(node: TreeNode, metric: "loc" | "complexity"): number {
  if (metric === "loc") {
    return Math.max(0.1, node.value ?? 0);
  }
  return Math.max(0.1, node.complexity ?? 0);
}

function buildTreemap() {
  if (!svgRef.value) return;
  const svg = d3.select<SVGSVGElement, unknown>(svgRef.value);
  const { width } = svgRef.value.getBoundingClientRect();
  const viewportWidth = Math.max(280, width);
  const height = Math.max(320, Math.min(viewportWidth * 0.72, 600));
  const themeStyles = window.getComputedStyle(document.body);
  const labelColor = themeStyles.getPropertyValue("--color-text-primary") || "#0f172a";
  const subLabelColor = themeStyles.getPropertyValue("--color-text-secondary") || "#1e293b";

  svg.attr("viewBox", `0 0 ${viewportWidth} ${height}`).attr("height", `${height}`);
  svg.selectAll("*").remove();

  if (!props.codeUnits.length) {
    return;
  }

  const hierarchy = d3
    .hierarchy<TreeNode>(buildHierarchy(props.codeUnits))
    .sum((d) => metricValue(d, sizeMetric.value))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  const treemapLayout = d3.treemap<TreeNode>().size([viewportWidth, height]).paddingInner(3).paddingOuter(6);
  const treemapRoot = treemapLayout(hierarchy);

  const nodes = treemapRoot.leaves();
  const metrics = nodes.map((node) => metricValue(node.data, colorMetric.value));
  const maxMetric = Math.max(1, ...metrics);
  const colorScale = (() => {
    if (colorMetric.value === "complexity") {
      return d3.scaleSequential<string>(d3.interpolateRgb("#f0f9ff", "#2563eb")).domain([0, maxMetric]);
    }
    return d3.scaleSequential<string>(d3.interpolateRgb("#ecfdf5", "#0f766e")).domain([0, maxMetric]);
  })();

  const cell = svg
    .selectAll<SVGGElement, d3.HierarchyRectangularNode<TreeNode>>("g")
    .data(nodes)
    .join("g")
    .attr("transform", (d) => `translate(${d.x0},${d.y0})`);

  cell
    .append("rect")
    .attr("width", (d) => Math.max(0, d.x1 - d.x0))
    .attr("height", (d) => Math.max(0, d.y1 - d.y0))
    .attr("rx", 12)
    .attr("ry", 12)
    .attr("fill", (d) => colorScale(metricValue(d.data, colorMetric.value)))
    .attr("fill-opacity", 0.9);

  if (showLabels.value) {
    const label = cell
      .append("g")
      .attr(
        "opacity",
        (d) => ((d.x1 - d.x0) * (d.y1 - d.y0) > 4200 ? 1 : 0),
      );

    label
      .append("text")
      .attr("x", 14)
      .attr("y", 24)
      .attr("fill", labelColor)
      .attr("font-size", 13)
      .attr("font-weight", 700)
      .text((d) => d.data.name);

    label
      .append("text")
      .attr("x", 14)
      .attr("y", 40)
      .attr("fill", subLabelColor)
      .attr("font-size", 11)
      .attr("font-weight", 500)
      .text((d) => `${d.data.value ?? 0} LOC · ${(d.data.complexity ?? 0).toFixed(1)} CC`)
      .attr(
        "opacity",
        (d) => ((d.x1 - d.x0) * (d.y1 - d.y0) > 6000 ? 1 : 0),
      );
  }

  cell
    .append("title")
    .text((d) => `${d.data.path}\n${d.data.value ?? 0} LOC\nComplexity: ${(d.data.complexity ?? 0).toFixed(2)}`);

  cell
    .on("mouseenter", (event, node) => showTooltip(event as MouseEvent, node))
    .on("mousemove", (event) => moveTooltip(event as MouseEvent))
    .on("mouseleave", () => hideTooltip());
}

function setup() {
  buildTreemap();
  if (svgRef.value) {
    resizeObserver = new ResizeObserver(() => buildTreemap());
    resizeObserver.observe(svgRef.value);
  }
}

onMounted(setup);

watch(
  () => props.codeUnits,
  () => {
    hideTooltip();
    buildTreemap();
  },
  { deep: true },
);

watch([sizeMetric, colorMetric, showLabels], () => buildTreemap());

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  hideTooltip();
});
</script>

<template>
  <div class="space-y-4">
    <div class="grid gap-3 rounded-2xl border border-theme-soft bg-[var(--color-surface-muted)] px-4 py-3 text-xs text-secondary md:grid-cols-[minmax(0,1fr)_auto_auto]">
      <div class="flex flex-col justify-center">
        <p class="font-semibold uppercase tracking-[0.4em]">Treemap Controls</p>
        <p class="text-[11px] tracking-[0.2em]">{{ legendLabel }}</p>
      </div>
      <div class="flex items-center justify-end gap-2">
        <label class="flex items-center gap-2 rounded-full border border-theme-soft bg-[var(--color-surface)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-secondary">
          <input v-model="showLabels" type="checkbox" class="accent-sky-500" />
          Labels
        </label>
      </div>
      <div class="flex flex-wrap items-center justify-end gap-2">
        <div class="flex items-center gap-1 rounded-full border border-theme-soft bg-[var(--color-surface)] px-2 py-1">
          <span class="text-[10px] uppercase tracking-[0.25em] text-secondary">Size</span>
          <button
            class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.25em]"
            :class="sizeMetric === 'loc' ? 'bg-sky-500/25 text-primary shadow-inner shadow-sky-500/20' : 'text-secondary hover:text-primary'"
            type="button"
            @click="sizeMetric = 'loc'"
          >
            LOC
          </button>
          <button
            class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.25em]"
            :class="sizeMetric === 'complexity' ? 'bg-sky-500/25 text-primary shadow-inner shadow-sky-500/20' : 'text-secondary hover:text-primary'"
            type="button"
            @click="sizeMetric = 'complexity'"
          >
            Complexity
          </button>
        </div>
        <div class="flex items-center gap-1 rounded-full border border-theme-soft bg-[var(--color-surface)] px-2 py-1">
          <span class="text-[10px] uppercase tracking-[0.25em] text-secondary">Color</span>
          <button
            class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.25em]"
            :class="colorMetric === 'complexity' ? 'bg-emerald-500/25 text-primary shadow-inner shadow-emerald-500/20' : 'text-secondary hover:text-primary'"
            type="button"
            @click="colorMetric = 'complexity'"
          >
            Complexity
          </button>
          <button
            class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.25em]"
            :class="colorMetric === 'loc' ? 'bg-emerald-500/25 text-primary shadow-inner shadow-emerald-500/20' : 'text-secondary hover:text-primary'"
            type="button"
            @click="colorMetric = 'loc'"
          >
            LOC
          </button>
        </div>
      </div>
    </div>

    <div ref="containerRef" class="relative overflow-hidden rounded-3xl border border-theme-soft bg-[var(--color-surface-muted)] shadow-inner shadow-black/5">
      <svg ref="svgRef" class="w-full"></svg>
      <transition name="fade">
        <div
          v-if="tooltip.visible"
          class="pointer-events-none absolute z-20 max-w-xs rounded-2xl border border-theme-soft px-4 py-3 text-xs shadow-xl"
          :style="{ top: `${tooltip.y}px`, left: `${tooltip.x}px`, background: 'var(--color-surface)' }"
        >
          <p class="text-[11px] font-semibold uppercase tracking-[0.4em] text-secondary">{{ tooltip.path }}</p>
          <p class="mt-2 text-sm font-semibold text-primary">{{ tooltip.name }}</p>
          <p class="mt-1 text-xs text-secondary">{{ tooltip.metrics }}</p>
        </div>
      </transition>
    </div>
  </div>
</template>
