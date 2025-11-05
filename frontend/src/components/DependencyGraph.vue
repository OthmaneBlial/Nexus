<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as d3 from "d3";
import type { D3DragEvent } from "d3";

import type { Dependency } from "@/types/udm";

const props = defineProps<{
  dependencies: Dependency[];
}>();

const wrapperRef = ref<HTMLDivElement | null>(null);
const svgRef = ref<SVGSVGElement | null>(null);
let resizeObserver: ResizeObserver | null = null;
let simulation: d3.Simulation<GraphNode, GraphLink> | null = null;
let nodeSelection: d3.Selection<SVGGElement, GraphNode, SVGGElement, unknown> | null = null;

const selectedDependency = ref<Dependency | null>(null);
const hoveredDependencyId = ref<string | null>(null);
const filterType = ref<"ALL" | "DIRECT" | "TRANSITIVE">("ALL");

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  version?: string | null;
  type: string;
  radius: number;
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  type: string;
}

const stats = computed(() => {
  const total = props.dependencies.length;
  const direct = props.dependencies.filter((dep) => dep.type === "DIRECT").length;
  return {
    total,
    direct,
    transitive: total - direct,
  };
});

const sortedDependencies = computed(() =>
  [...props.dependencies].sort((a, b) => {
    if (a.type === b.type) {
      return a.name.localeCompare(b.name);
    }
    return a.type === "DIRECT" ? -1 : 1;
  }),
);

const filteredDependencies = computed(() => {
  if (filterType.value === "ALL") {
    return sortedDependencies.value;
  }
  return sortedDependencies.value.filter((dep) => dep.type === filterType.value);
});

const legendColors: Record<string, string> = {
  ROOT: "bg-sky-400",
  DIRECT: "bg-emerald-400",
  TRANSITIVE: "bg-fuchsia-400",
};

function updateNodeStyles() {
  if (!nodeSelection) return;
  const circles = nodeSelection.selectAll<SVGCircleElement, GraphNode>("circle");
  circles.attr("stroke-width", (d) => {
    if (selectedDependency.value?.id === d.id) return 4;
    if (hoveredDependencyId.value === d.id) return 3;
    return d.type === "ROOT" ? 3 : 2;
  });

  circles.attr("fill-opacity", (d) => {
    if (selectedDependency.value && selectedDependency.value.id !== d.id) return 0.18;
    if (hoveredDependencyId.value && hoveredDependencyId.value !== d.id) return 0.25;
    return d.type === "ROOT" ? 0.4 : 0.3;
  });

  nodeSelection
    .selectAll<SVGTextElement, GraphNode>("text")
    .attr("font-weight", (d) => (selectedDependency.value?.id === d.id ? 700 : 600));
}

function buildGraph() {
  if (!svgRef.value) return;

  const svg = d3.select<SVGSVGElement, unknown>(svgRef.value);
  const width = wrapperRef.value?.getBoundingClientRect().width ?? svgRef.value.getBoundingClientRect().width;
  const viewportWidth = Math.max(520, width);
  const height = Math.max(520, Math.min(viewportWidth * 0.9, 640));
  const themeStyles = window.getComputedStyle(document.body);
  const textColor = themeStyles.getPropertyValue("--color-text-primary") || "#1f2937";
  const frameColor = themeStyles.getPropertyValue("--color-border-soft") || "#94a3b8";

  svg.attr("viewBox", `0 0 ${viewportWidth} ${height}`);
  svg.attr("height", `${height}`);
  svg.selectAll("*").remove();

  const nodes: GraphNode[] = [
    {
      id: "project-root",
      name: "Project Root",
      type: "ROOT",
      radius: 32,
    },
    ...props.dependencies.map((dep) => ({
      id: dep.id,
      name: dep.name,
      version: dep.version,
      type: dep.type,
      radius: dep.type === "DIRECT" ? 20 : 16,
    })),
  ];

  const links: GraphLink[] = props.dependencies.map((dep) => ({
    source: "project-root",
    target: dep.id,
    type: dep.type,
  }));

  const colorScale = d3
    .scaleOrdinal<string, string>()
    .domain(["ROOT", "DIRECT", "TRANSITIVE"])
    .range(["#38bdf8", "#34d399", "#a855f7"]);

  simulation?.stop();
  simulation = d3
    .forceSimulation(nodes)
    .force(
      "link",
      d3
        .forceLink<GraphNode, GraphLink>(links)
        .id((d) => d.id)
        .distance(140),
    )
    .force("charge", d3.forceManyBody().strength(-260))
    .force("center", d3.forceCenter(viewportWidth / 2, height / 2))
    .force("collision", d3.forceCollide<GraphNode>().radius((d) => d.radius + 8));

  svg
    .append("defs")
    .append("marker")
    .attr("id", "dependency-arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 12)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("fill", frameColor)
    .attr("d", "M0,-5L10,0L0,5");

  const link = svg
    .append("g")
    .attr("stroke", frameColor)
    .attr("stroke-opacity", 0.4)
    .attr("stroke-width", 1.2)
    .selectAll<SVGLineElement, GraphLink>("line")
    .data(links)
    .join("line")
    .attr("stroke-dasharray", (d) => (d.type === "TRANSITIVE" ? "4 3" : ""))
    .attr("marker-end", "url(#dependency-arrow)");

  nodeSelection = svg
    .append("g")
    .selectAll<SVGGElement, GraphNode>("g")
    .data(nodes)
    .join("g")
    .call(
      d3
        .drag<SVGGElement, GraphNode>()
        .on("start", (event: D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) => {
          if (!event.active) simulation?.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event: D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event: D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) => {
          if (!event.active) simulation?.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }),
    )
    .on("click", (_, d) => {
      if (d.id === "project-root") {
        selectedDependency.value = null;
      } else {
        selectedDependency.value = props.dependencies.find((dep) => dep.id === d.id) ?? null;
      }
    });

  nodeSelection
    .append("circle")
    .attr("r", (d) => d.radius)
    .attr("fill", (d) => colorScale(d.type))
    .attr("fill-opacity", (d) => (d.type === "ROOT" ? 0.4 : 0.3))
    .attr("stroke", (d) => colorScale(d.type))
    .attr("stroke-width", (d) => (d.type === "ROOT" ? 3 : 2));

  nodeSelection
    .append("text")
    .attr("dy", ".35em")
    .attr("text-anchor", "middle")
    .attr("font-size", 11)
    .attr("font-weight", 600)
    .attr("fill", textColor)
    .text((d) => d.name);

  nodeSelection.append("title").text((d) => (d.version ? `${d.name}@${d.version}` : d.name));

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => (d.source as GraphNode).x ?? 0)
      .attr("y1", (d) => (d.source as GraphNode).y ?? 0)
      .attr("x2", (d) => (d.target as GraphNode).x ?? 0)
      .attr("y2", (d) => (d.target as GraphNode).y ?? 0);

    nodeSelection?.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
  });

  updateNodeStyles();
}

function setup() {
  buildGraph();
  if (wrapperRef.value) {
    resizeObserver = new ResizeObserver(() => buildGraph());
    resizeObserver.observe(wrapperRef.value);
  }
}

onMounted(setup);

watch(
  () => props.dependencies,
  () => {
    selectedDependency.value = null;
    buildGraph();
  },
  { deep: true },
);

watch([selectedDependency, hoveredDependencyId], () => updateNodeStyles());

onBeforeUnmount(() => {
  simulation?.stop();
  resizeObserver?.disconnect();
});
</script>

<template>
  <div ref="wrapperRef" class="space-y-4" :style="{ background: 'var(--color-surface-muted)', borderRadius: '1.5rem', padding: '1.5rem', border: '1px solid var(--color-border-soft)' }">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.35em] text-secondary">Dependency Graph</p>
        <p class="text-xs text-secondary">Interact with nodes to highlight related metadata.</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.3em] text-secondary">
        <span class="flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-full bg-sky-400"></span> Root</span>
        <span class="flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-full bg-emerald-400"></span> Direct</span>
        <span class="flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-full bg-fuchsia-400"></span> Transitive</span>
      </div>
    </div>

    <div class="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <div class="relative overflow-hidden rounded-3xl border border-theme-soft bg-[var(--color-surface)] shadow-inner shadow-black/5">
        <svg ref="svgRef" class="w-full"></svg>
        <button
          class="absolute right-4 top-4 rounded-full border border-theme-soft bg-[var(--color-surface)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.3em] text-secondary transition hover:text-primary"
          type="button"
          @click="selectedDependency = null"
        >
          Reset Focus
        </button>
      </div>

      <aside class="space-y-4">
        <div class="flex items-center justify-between rounded-2xl border border-theme-soft bg-[var(--color-surface)] px-4 py-3 text-xs text-secondary">
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-[0.35em]">Total</p>
            <p class="mt-1 text-lg font-semibold text-primary">{{ stats.total }}</p>
          </div>
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-[0.35em]">Direct</p>
            <p class="mt-1 text-lg font-semibold text-primary">{{ stats.direct }}</p>
          </div>
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-[0.35em]">Transitive</p>
            <p class="mt-1 text-lg font-semibold text-primary">{{ stats.transitive }}</p>
          </div>
        </div>

        <div class="space-y-3 rounded-2xl border border-theme-soft bg-[var(--color-surface)] p-4">
          <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] font-semibold uppercase tracking-[0.3em] text-secondary">
            <span>Dependencies</span>
            <div class="flex items-center gap-2">
              <button
                class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em]"
      :class="filterType === 'ALL' ? 'bg-sky-500/25 text-primary shadow-inner shadow-sky-500/20' : 'text-secondary hover:text-primary'"
                type="button"
                @click="filterType = 'ALL'"
              >
                All
              </button>
              <button
                class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em]"
      :class="filterType === 'DIRECT' ? 'bg-emerald-500/25 text-primary shadow-inner shadow-emerald-500/20' : 'text-secondary hover:text-primary'"
                type="button"
                @click="filterType = 'DIRECT'"
              >
                Direct
              </button>
              <button
                class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em]"
      :class="filterType === 'TRANSITIVE' ? 'bg-fuchsia-500/25 text-primary shadow-inner shadow-fuchsia-500/20' : 'text-secondary hover:text-primary'"
                type="button"
                @click="filterType = 'TRANSITIVE'"
              >
                Transitive
              </button>
            </div>
          </div>

          <ul class="max-h-72 space-y-2 overflow-y-auto pr-1 text-sm">
            <li
              v-for="dependency in filteredDependencies"
              :key="dependency.id"
              class="rounded-2xl border border-theme-soft bg-[var(--color-surface-muted)] transition hover:border-theme"
            >
              <button
                class="flex w-full items-start justify-between gap-3 rounded-2xl px-4 py-3 text-left"
                type="button"
                @click="selectedDependency = dependency"
                @mouseenter="hoveredDependencyId = dependency.id"
                @mouseleave="hoveredDependencyId = null"
              >
                <div>
                  <p class="text-sm font-semibold text-primary">{{ dependency.name }}</p>
                  <p class="text-[11px] uppercase tracking-[0.3em] text-secondary">{{ dependency.type }}</p>
                  <p v-if="dependency.version" class="mt-1 text-xs text-secondary">Version · {{ dependency.version }}</p>
                  <p v-if="dependency.license" class="mt-1 text-xs text-secondary">License · {{ dependency.license }}</p>
                  <p v-if="dependency.vulnerabilities?.length" class="mt-1 text-xs text-rose-500">
                    Vulnerabilities · {{ dependency.vulnerabilities.join(", ") }}
                  </p>
                </div>
                <span
                  class="mt-1 h-2 w-2 rounded-full"
                  :class="legendColors[dependency.type]"
                ></span>
              </button>
            </li>
            <li v-if="filteredDependencies.length === 0" class="rounded-2xl border border-dashed border-theme-soft px-4 py-6 text-center text-[11px] uppercase tracking-[0.35em] text-secondary">
              No dependencies
            </li>
          </ul>
        </div>

        <div v-if="selectedDependency" class="rounded-2xl border border-theme-soft bg-[var(--color-surface)] p-4 text-sm text-secondary">
          <p class="text-[11px] font-semibold uppercase tracking-[0.35em] text-secondary">Focused Dependency</p>
          <p class="mt-2 text-lg font-semibold text-primary">{{ selectedDependency.name }}</p>
          <p class="text-xs uppercase tracking-[0.3em]">{{ selectedDependency.type }}</p>
          <ul class="mt-3 space-y-2 text-xs">
            <li v-if="selectedDependency.version">
              <span class="font-semibold text-primary">Version:</span> {{ selectedDependency.version }}
            </li>
            <li v-if="selectedDependency.license">
              <span class="font-semibold text-primary">License:</span> {{ selectedDependency.license }}
            </li>
            <li v-if="selectedDependency.vulnerabilities?.length">
              <span class="font-semibold text-primary">Vulnerabilities:</span> {{ selectedDependency.vulnerabilities.join(", ") }}
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>
