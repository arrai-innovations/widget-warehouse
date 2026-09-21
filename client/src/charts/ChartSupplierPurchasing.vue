<script setup>
import { CurveType } from "@unovis/ts";
import { VisAxis, VisCrosshair, VisLine, VisScatter, VisTooltip, VisXYContainer } from "@unovis/vue";
import "@vueda/theme/vueda-tailwind/unovis.css";
import { computed } from "vue";

import { amountFormat, chartRows, dateFormat } from "@/charts/purchasing.js";

const props = defineProps({ series: { type: Array, required: true } });
const rows = computed(() => chartRows(props.series));
const x = (row) => row.timestamp;
const y = computed(() => props.series.map((supplier) => (row) => row[supplier.id]));
const color = (datum, index) => props.series[index].color;
const dash = (datum, index) => props.series[index].dash;
const formatTick = (value) => dateFormat.format(value);
const formatAmount = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });
const ticks = computed(() => rows.value.filter((row, index) => index % Math.ceil(rows.value.length / 5) === 0).map(x));
const tooltip = (row) => {
    const node = document.createElement("div");
    node.style.fontSize = "var(--vueda-text-supporting)";
    const heading = document.createElement("strong");
    heading.textContent = `Week of ${dateFormat.format(row.timestamp)}`;
    node.append(heading);
    for (const supplier of props.series) {
        const line = document.createElement("div");
        line.textContent = `${supplier.name}: ${amountFormat.format(row.amounts[supplier.id])}`;
        node.append(line);
    }
    return node;
};
</script>

<template>
    <div
        role="img"
        aria-label="Weekly purchase order value by supplier. Exact values and order links follow in the data table."
    >
        <VisXYContainer class="unovis-vueda" :data="rows" :height="300" :y-domain="[0, undefined]">
            <VisLine
                :x="x"
                :y="y"
                :color="color"
                :line-dash-array="dash"
                :line-width="2.5"
                :curve-type="CurveType.Linear"
            />
            <VisScatter :x="x" :y="y" :color="color" :size="5" />
            <VisAxis
                type="x"
                :tick-values="ticks"
                :tick-format="formatTick"
                :grid-line="false"
                :domain-line="false"
                :tick-line="false"
            />
            <VisAxis
                type="y"
                :tick-format="formatAmount.format"
                :num-ticks="5"
                :domain-line="false"
                :tick-line="false"
            />
            <VisCrosshair :x="x" :y="y" :color="color" :template="tooltip" />
            <VisTooltip />
        </VisXYContainer>
    </div>
</template>
