import TheApp from "./TheApp.vue";
import { getRouter } from "./router/index.js";
import { config as faConfig } from "@fortawesome/fontawesome-svg-core";
import "@fortawesome/fontawesome-svg-core/styles.css";
import {
    faAnglesLeft,
    faAnglesRight,
    faCaretDown,
    faCaretUp,
    faCheck,
    faChevronLeft,
    faChevronRight,
    faCircle,
    faCircleInfo,
    faDownload,
    faEllipsis,
    faGripVertical,
    faMinus,
    faPlus,
    faSpinner,
    faTriangleExclamation,
    faXmark,
} from "@fortawesome/sharp-duotone-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import vuedaTailwind from "@vueda/theme/vueda-tailwind/index.js";
import { setIcons } from "@vueda/use/useIcons.js";
import { setTheme } from "@vueda/use/useTheme.js";
import { setupDefaultListCrud } from "@vueda/utils/listCrud.js";
import { setupDefaultObjectCrud } from "@vueda/utils/objectCrud.js";
import { createPinia } from "pinia";
import { createApp } from "vue";

import { setupModelConfig } from "@/setupModelConfig.js";

faConfig.autoAddCss = false;

setTheme(vuedaTailwind);
setIcons({
    Checkbox: {
        check: { component: FontAwesomeIcon, props: { icon: faCheck } },
        indeterminate: { component: FontAwesomeIcon, props: { icon: faMinus } },
    },
    Default: {
        anglesLeft: { component: FontAwesomeIcon, props: { icon: faAnglesLeft } },
        anglesRight: { component: FontAwesomeIcon, props: { icon: faAnglesRight } },
        caretDown: { component: FontAwesomeIcon, props: { icon: faCaretDown } },
        caretUp: { component: FontAwesomeIcon, props: { icon: faCaretUp } },
        check: { component: FontAwesomeIcon, props: { icon: faCheck } },
        chevronLeft: { component: FontAwesomeIcon, props: { icon: faChevronLeft } },
        chevronRight: { component: FontAwesomeIcon, props: { icon: faChevronRight } },
        circle: { component: FontAwesomeIcon, props: { icon: faCircle } },
        close: { component: FontAwesomeIcon, props: { icon: faXmark } },
        download: { component: FontAwesomeIcon, props: { icon: faDownload } },
        ellipsis: { component: FontAwesomeIcon, props: { icon: faEllipsis } },
        gripVertical: { component: FontAwesomeIcon, props: { icon: faGripVertical } },
        info: { component: FontAwesomeIcon, props: { icon: faCircleInfo } },
        loading: { component: FontAwesomeIcon, props: { icon: faSpinner, spin: true } },
        plus: { component: FontAwesomeIcon, props: { icon: faPlus } },
        triangleExclamation: { component: FontAwesomeIcon, props: { icon: faTriangleExclamation } },
    },
});
setupDefaultListCrud();
setupDefaultObjectCrud();

const app = createApp(TheApp);
const pinia = createPinia();

app.use(pinia);
setupModelConfig(pinia);

const router = getRouter(app, pinia);

app.use(router);

app.mount("#the-app");

export default app;
