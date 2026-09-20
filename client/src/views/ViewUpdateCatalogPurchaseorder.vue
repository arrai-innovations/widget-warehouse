<script setup>
import ViewUpdate from "@vueda/views/ViewUpdate.vue";

import { usePurchasePriceDefaults } from "@/use/usePurchasePriceDefaults.js";

defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
const attachPriceDefaults = usePurchasePriceDefaults();
</script>
<template><ViewUpdate :app="app" :model="model" :pk="pk" @form-context="attachPriceDefaults" /></template>
