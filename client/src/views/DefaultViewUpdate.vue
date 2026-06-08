<script setup>
import ViewUpdate from "@vueda/views/ViewUpdate.vue";

defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
defineOptions({ inheritAttrs: false });
</script>

<template>
    <ViewUpdate v-bind="{ ...$props, ...$attrs }">
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </ViewUpdate>
</template>
