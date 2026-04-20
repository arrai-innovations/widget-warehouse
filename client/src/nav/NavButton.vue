<script setup>
import Button from "@vueda/controls/button/Button.vue";
import Tooltip from "@vueda/shell/tooltip/Tooltip.vue";
import TooltipContent from "@vueda/shell/tooltip/TooltipContent.vue";
import TooltipProvider from "@vueda/shell/tooltip/TooltipProvider.vue";
import TooltipTrigger from "@vueda/shell/tooltip/TooltipTrigger.vue";

defineProps({
    showTooltip: {
        type: Boolean,
        default: false,
    },
});
</script>

<template>
    <TooltipProvider>
        <Tooltip :disabled="!showTooltip">
            <TooltipTrigger as-child>
                <Button v-bind="$attrs">
                    <slot v-bind="$props"></slot>
                </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
                <slot name="tooltip" v-bind="$props"></slot>
            </TooltipContent>
        </Tooltip>
    </TooltipProvider>
</template>
