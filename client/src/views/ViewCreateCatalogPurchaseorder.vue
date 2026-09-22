<script setup>
import { usePurchasePriceDefaults } from "@/use/usePurchasePriceDefaults.js";
import DefaultViewCreate from "@/views/DefaultViewCreate.vue";

defineProps({ app: { type: String, required: true }, model: { type: String, required: true } });
const attachPriceDefaults = usePurchasePriceDefaults();
</script>
<!-- The field layout comes from formLayouts.js through DefaultViewCreate. -->
<template><DefaultViewCreate :app="app" :model="model" @form-context="attachPriceDefaults" /></template>
