<script setup>
import ViewUpdate from "@vueda/views/ViewUpdate.vue";
import { computed } from "vue";

import SectionedFormFields from "@/form/SectionedFormFields.vue";
import { getFormLayout } from "@/form/formLayouts.js";
import { useReadFallback } from "@/use/useReadFallback.js";

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
defineOptions({ inheritAttrs: false });
const readFallback = useReadFallback(props);
const formLayout = computed(() => getFormLayout(props.app, props.model));
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
        <!-- The same layout as create, so the two forms do not drift apart. -->
        <template v-if="formLayout && !$slots.fields" #fields="{ formModel, fieldNames }">
            <SectionedFormFields :field-names="fieldNames" :form-model="formModel" :sections="formLayout" />
        </template>
    </ViewUpdate>
</template>
