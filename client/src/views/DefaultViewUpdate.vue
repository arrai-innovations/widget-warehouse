<script setup>
import ViewUpdate from "@vueda/views/ViewUpdate.vue";

import { useReadFallback } from "@/use/useReadFallback.js";

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
defineOptions({ inheritAttrs: false });
const readFallback = useReadFallback(props);
</script>

<template>
    <ViewUpdate
        v-bind="{ ...$props, ...$attrs }"
        @object="readFallback.object = $event"
        @loading="readFallback.loading = $event"
    >
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </ViewUpdate>
</template>
