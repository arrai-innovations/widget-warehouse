<script setup>
/**
 * The order pipeline, drawn with Unovis.
 *
 * One measure (how many orders) across a handful of categories (which state they are in),
 * which is a single series: every bar is the accent colour, and there is no legend to
 * write because the card's title already says what is plotted. Giving each state its own
 * hue would encode the category twice, once as the bar's position and once as its colour.
 *
 * The chart is the shape only. The exact counts, and the links into the filtered list,
 * stay in the list beside it, so nothing here is reachable by pointer alone.
 *
 * Unovis is imported by this component and nowhere else, and the dashboard loads the
 * component asynchronously, so a page that draws no chart never pays for the library.
 */
import { Direction, Orientation, StackedBar } from "@unovis/ts";
import { VisAxis, VisStackedBar, VisTooltip, VisXYContainer } from "@unovis/vue";
import { computed } from "vue";

import "@/charts/unovisVuedaTheme.css";

const props = defineProps({
    // `{ code, name, count }` per state, in workflow order.
    states: {
        type: Array,
        required: true,
    },
});

// A bar is capped well below its band so the space between bars, rather than a stroke
// around them, is what separates them. The axis band is added to the height rather than
// taken out of it: a container sized to the plot alone crops its own tick labels.
const BAR_MAX_WIDTH = 20;
const BAND_HEIGHT = 34;
const AXIS_HEIGHT = 28;

const height = computed(() => props.states.length * BAND_HEIGHT + AXIS_HEIGHT);

// Unovis plots numbers, so each state is placed at its index and the category axis turns
// the index back into a name. The server sends the states in workflow order, so an
// index is the position an order passes through on its way out of the warehouse.
const position = (state, index) => index;
const count = (state) => state.count;

const positions = computed(() => props.states.map((state, index) => index));
const stateName = (index) => props.states[index]?.name ?? "";

const busiest = computed(() => Math.max(1, ...props.states.map((state) => state.count)));

// Whole orders, so whole ticks. Left to choose for itself the axis offers halves whenever
// the busiest state holds only two or three orders.
const countTicks = computed(() => {
    const step = Math.max(1, Math.ceil(busiest.value / 4));
    const ticks = [];
    for (let value = 0; value <= busiest.value; value += step) {
        ticks.push(value);
    }
    return ticks;
});

// The tooltip gets an element rather than a string, because Unovis assigns a string
// through innerHTML and these names come out of the database.
//
// A trigger is also handed the bar's internal record rather than the row it was built
// from, which is why this reaches through `.datum`. Unovis's event map does the opposite
// and unwraps it first, so the two callbacks disagree about what a datum is.
const triggers = {
    [StackedBar.selectors.bar]: (bar) => {
        const state = bar.datum;
        const tip = document.createElement("span");
        // Unovis gives the tooltip no font-size variable of its own, so without this it
        // inherits the page's body size and sits a step larger than the chart it explains.
        tip.style.fontSize = "var(--vueda-text-supporting)";
        tip.textContent = `${state.name}: ${state.count}`;
        return tip;
    },
};
</script>

<template>
    <VisXYContainer
        class="unovis-vueda"
        :data="states"
        :height="height"
        :x-domain="[0, busiest]"
        :y-direction="Direction.South"
    >
        <VisStackedBar
            :x="position"
            :y="count"
            :orientation="Orientation.Horizontal"
            :bar-max-width="BAR_MAX_WIDTH"
            :rounded-corners="4"
        />
        <VisAxis type="x" :tick-values="countTicks" :grid-line="true" :domain-line="false" :tick-line="false" />
        <VisAxis
            type="y"
            :tick-values="positions"
            :tick-format="stateName"
            :grid-line="false"
            :domain-line="false"
            :tick-line="false"
        />
        <VisTooltip :triggers="triggers" />
    </VisXYContainer>
</template>
