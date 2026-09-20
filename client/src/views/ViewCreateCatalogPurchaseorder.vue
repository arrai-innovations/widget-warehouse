<script setup>
import ViewCreate from "@vueda/views/ViewCreate.vue";

import { usePurchasePriceDefaults } from "@/use/usePurchasePriceDefaults.js";

defineProps({ app: { type: String, required: true }, model: { type: String, required: true } });
const attachPriceDefaults = usePurchasePriceDefaults();
</script>
<template><ViewCreate :app="app" :model="model" @form-context="attachPriceDefaults" /></template>
