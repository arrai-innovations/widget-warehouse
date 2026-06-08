<script setup>
import ErrorDisplay from "@vueda/components/ErrorDisplay.vue";
import FormModel from "@vueda/components/FormModel.vue";
import LinkModelView from "@vueda/components/LinkModelView.vue";
import LoadingSpinnerInline from "@vueda/components/LoadingSpinnerInline.vue";
import PageActions from "@vueda/components/PageActions.vue";
import StickyBar from "@vueda/components/StickyBar.vue";
import Button from "@vueda/controls/button/Button.vue";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import { useViewCreate } from "@vueda/use/useViewCreate.js";
import { memoizedStartCase } from "@vueda/utils/case.js";
import { onMounted, toRef } from "vue";

defineOptions({ inheritAttrs: false });

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    variant: { type: String, default: "default" },
    formModelVariant: { type: String, default: "default" },
    class: { type: [String, Array, Object], default: () => [] },
    formProps: { type: Object, default: () => ({}) },
    fieldProps: { type: Object, default: () => ({}) },
    widgetProps: { type: Object, default: () => ({}) },
    submitFields: { type: Array, default: undefined },
    redirectAfter: {
        type: String,
        default: "update",
        validator: (value) => ["list", "update", "read"].includes(value),
    },
});
const emit = defineEmits(["form-object", "form-context"]);

const { formContext, objectForm, instance, actions } = useViewCreate(props);

// Contribute the page title and loading state to the layout's ThePageTitle display.
usePageTitle(() => ({ title: instance.titleStr, loading: instance.pageLoading }));

onMounted(() => {
    emit(
        "form-object",
        toRef(() => formContext.state.values),
    );
    emit("form-context", formContext);
});
</script>
<template>
    <div :class="props.class">
        <!-- Page-level actions teleport into the layout's ThePageTitle action zone. -->
        <page-actions>
            <template v-for="actionName in actions.nonDetailActions" :key="actionName">
                <slot
                    :app="app"
                    :label="memoizedStartCase(actionName)"
                    :model="model"
                    name="targetless-action-button"
                    :view="actionName"
                >
                    <link-model-view
                        :app="app"
                        :label="memoizedStartCase(actionName)"
                        :model="model"
                        :view="actionName"
                    />
                </slot>
            </template>
        </page-actions>
        <sticky-bar class="w-full">
            <div data-qa="update-action-buttons">
                <slot
                    :form="instance.formId"
                    label="Submit"
                    :loading="objectForm.state.loading"
                    :modified="formContext.state.anyModified"
                    name="submit-button"
                    type="submit"
                >
                    <Button :form="instance.formId" :disabled="objectForm.state.loading" type="submit">
                        <LoadingSpinnerInline v-if="objectForm.state.loading" />
                        Submit
                    </Button>
                </slot>
            </div>
        </sticky-bar>
        <div>
            <error-display
                :error="instance.combinedError"
                :errored="instance.combinedErrored"
                :ignore-form-validation-errors="true"
                :while-text="instance.combinedWhileText"
            />
            <form v-bind="$attrs" :id="instance.formId" @submit.prevent="objectForm.submit">
                <form-model
                    :app="app"
                    v-bind="instance.combinedFormProps"
                    :field-props="props.fieldProps"
                    :model="model"
                    :variant="formModelVariant"
                    :view="'create'"
                    :widget-props="props.widgetProps"
                >
                    <template v-for="(_, slot) in $slots" #[slot]="slotProps">
                        <slot :name="slot" v-bind="slotProps || {}" />
                    </template>
                </form-model>
            </form>
        </div>
    </div>
</template>
