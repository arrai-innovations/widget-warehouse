<script setup>
import { usePageTitle } from "@vueda/use/usePageTitle.js";

// Contribute this custom view's title to the layout's ThePageTitle display.
usePageTitle(() => ({ title: "Widget Warehouse" }));
</script>

<template>
    <p>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec a diam lectus. Sed sit amet ipsum mauris.
        Maecenas congue ligula ac quam viverra nec consectetur ante hendrerit. Donec et mollis dolor. Praesent et diam
        eget libero egestas mattis sit amet vitae augue. Nam tincidunt congue enim, ut porta lorem lacinia consectetur.
    </p>
</template>
