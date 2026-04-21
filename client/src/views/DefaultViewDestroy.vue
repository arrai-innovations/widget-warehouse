<script setup>
import ViewDestroy from "@vueda/views/ViewDestroy.vue";

defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
defineOptions({ inheritAttrs: false });
</script>

<template>
    <ViewDestroy v-bind="{ ...$props, ...$attrs }">
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </ViewDestroy>
</template>
