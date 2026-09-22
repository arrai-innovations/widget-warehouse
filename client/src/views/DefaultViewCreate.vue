<script setup>
import ViewCreate from "@vueda/views/ViewCreate.vue";
import { computed } from "vue";

import SectionedFormFields from "@/form/SectionedFormFields.vue";
import { getFormLayout } from "@/form/formLayouts.js";

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
});
defineOptions({ inheritAttrs: false });
const formLayout = computed(() => getFormLayout(props.app, props.model));
</script>

<template>
    <ViewCreate v-bind="{ ...$props, ...$attrs }">
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
        <!-- The fields slot replaces FormModel's default one-field-per-row loop. -->
        <template v-if="formLayout && !$slots.fields" #fields="{ formModel, fieldNames }">
            <SectionedFormFields :field-names="fieldNames" :form-model="formModel" :sections="formLayout" />
        </template>
    </ViewCreate>
</template>
