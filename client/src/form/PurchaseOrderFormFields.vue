<script setup>
import FieldRenderer from "@vueda/form/form-model/FieldRenderer.vue";
import FormGrid from "@vueda/form/layout/FormGrid.vue";
import FormSection from "@vueda/form/layout/FormSection.vue";
import FormSectionTitle from "@vueda/form/layout/FormSectionTitle.vue";
import { computed } from "vue";

/**
 * Sectioned, multi-column field layout for the purchase order create and update forms.
 *
 * VUEDA's default form is one full-width field per row, which is the right default for a
 * model whose field list is unknown but a poor fit for an order: five short header fields,
 * a line-item inline that wants the whole width, and read-only server-maintained values
 * that should not compete with the fields an operator fills in.
 *
 * This is the composition path for that: `FormModel` exposes a `fields` slot that replaces
 * its default loop, and `FormSection` and `FormGrid` are the layout primitives meant to go
 * inside it. Spans are expressed as `data-col`, not as `col-span-*` classes, so the grid's
 * breakpoint and gaps stay in `FormGrid`'s theme entry and a re-skin can retarget every
 * form at once.
 *
 * Two shapes here are forced by the current VUEDA surface rather than chosen:
 *
 * - `FieldRenderer` spreads its own attributes into both the field and the widget, and
 *   `FormField` forwards only `class` onto the field wrapper, so a `data-col` set on a
 *   `FieldRenderer` lands on the input instead of the grid child. Each field is therefore
 *   wrapped in a plain `div` that carries the span.
 * - Anything not named in `SECTIONS` would silently vanish from the form, so the trailing
 *   section renders whatever the model gained since this file was written. It is empty
 *   today and exists so a new server field shows up somewhere instead of nowhere.
 */
defineOptions({
    // The `fields` slot binds the whole form-model context; none of it belongs on the DOM.
    inheritAttrs: false,
});

const props = defineProps({
    /** Form model context from `FormModel`'s `fields` slot. */
    formModel: {
        type: Object,
        required: true,
    },
    /** Non-expanded field names the form is rendering, from the same slot. */
    fieldNames: {
        type: [Array, Set],
        required: true,
    },
});

// Field name and the columns it claims at and above FormGrid's breakpoint, out of twelve.
// FormGrid stamps spans for 3, 4, 6, 8, and 9; anything else stays full width.
const SECTIONS = [
    {
        title: "Order",
        aside: "supplier and dates",
        fields: [
            ["reference", 4],
            ["supplier", 4],
            ["destination_warehouse", 4],
            ["order_date", 3],
            ["expected_arrival_date", 3],
        ],
    },
    {
        title: "Lines",
        aside: "at least one",
        fields: [["lines", 12]],
    },
    {
        title: "Value and state",
        aside: "server maintained",
        fields: [
            ["total_value", 4],
            ["workflow_state_name", 4],
            ["workflow_state_code", 4],
            ["valid_transitions", 12],
        ],
    },
    {
        title: "Record",
        aside: "server maintained",
        fields: [
            ["created_at", 6],
            ["updated_at", 6],
        ],
    },
];

const renderedFieldNames = computed(() => new Set(props.fieldNames));

// A section drops out entirely when config leaves none of its fields in the form, so a
// narrowed displayFields list does not leave a heading standing over nothing.
const sections = computed(() =>
    SECTIONS.map((section) => ({
        ...section,
        fields: section.fields.filter(([name]) => renderedFieldNames.value.has(name)),
    })).filter((section) => section.fields.length),
);

const placedFieldNames = new Set(SECTIONS.flatMap((section) => section.fields.map(([name]) => name)));

const unplacedFields = computed(() => [...renderedFieldNames.value].filter((name) => !placedFieldNames.has(name)));
</script>

<template>
    <FormSection v-for="section in sections" :key="section.title">
        <template #title>
            <FormSectionTitle>{{ section.title }}</FormSectionTitle>
        </template>
        <template #aside>{{ section.aside }}</template>
        <FormGrid>
            <div v-for="[name, columns] in section.fields" :key="name" :data-col="columns">
                <FieldRenderer :form-model="formModel" :form-model-name="name" />
            </div>
        </FormGrid>
    </FormSection>
    <FormSection v-if="unplacedFields.length">
        <template #title>
            <FormSectionTitle>Unplaced</FormSectionTitle>
        </template>
        <template #aside>not yet assigned a section</template>
        <FormGrid>
            <div v-for="name in unplacedFields" :key="name">
                <FieldRenderer :form-model="formModel" :form-model-name="name" />
            </div>
        </FormGrid>
    </FormSection>
</template>
