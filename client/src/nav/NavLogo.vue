<script setup>
import { RouterLink } from "vue-router";

const props = defineProps({
    animated: {
        type: Boolean,
        default: false,
    },
});
const animationClasses =
    "transition-all duration-200 ease-linear group-data-[collapsible=icon]:max-w-0 group-data-[collapsible=icon]:opacity-0";
const widgetClassesAnimated = props.animated ? `overflow-hidden max-w-20 ${animationClasses}` : undefined;
const warehouseClassesAnimated = props.animated ? `overflow-hidden max-w-30 pr-0.75 ${animationClasses}` : undefined;
const comClassesAnimated = props.animated ? `overflow-hidden max-w-15 ${animationClasses}` : undefined;
</script>

<template>
    <RouterLink
        to="/"
        aria-label="Widget Warehouse home"
        class="flex items-baseline [&>span]:inline-block [&>span]:align-top text-[#0077f7] group-data-[collapsible=icon]:tracking-[-0.0125em]"
        ><span class="font-bold">W</span
        ><span class="font-bold overflow-hidden max-w-20" :class="widgetClassesAnimated">idget </span
        ><span class="italic">W</span
        ><span class="italic overflow-hidden max-w-30 pr-0.75" :class="warehouseClassesAnimated">arehouse</span
        ><span class="text-sidebar-foreground" :class="comClassesAnimated">.com</span></RouterLink
    >
</template>

<style scoped></style>
