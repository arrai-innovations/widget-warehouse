import { requireInitialized, requireUnauth } from "@vueda/router/guards.js";
import { makeCRUDRoutes } from "@vueda/router/makeCrud.js";
import { setCrudComponents } from "@vueda/router/routerComponent.js";
import { getPascalCaseName } from "@vueda/utils/case.js";
import { createRouter, createWebHistory } from "vue-router";

function makeViewLoader(action) {
    return async ({ app, model }) => {
        try {
            return (await import(`@/views/View${action}${getPascalCaseName(app)}${getPascalCaseName(model)}.vue`))
                .default;
        } catch {
            return (await import(`@/views/DefaultView${action}.vue`)).default;
        }
    };
}

export function getRouter(app, pinia) {
    const crudComponents = {
        list: makeViewLoader("List"),
        create: makeViewLoader("Create"),
        read: makeViewLoader("Read"),
        update: makeViewLoader("Update"),
        destroy: makeViewLoader("Destroy"),
    };
    setCrudComponents(crudComponents);

    const router = createRouter({
        history: createWebHistory(import.meta.env.BASE_URL),
        routes: [],
    });

    const routes = [
        {
            path: "/",
            name: "home",
            redirect: { name: "sign-in" },
        },
        {
            path: "/sign-in/",
            name: "sign-in",
            component: () => import("@/views/ViewSignIn.vue"),
            meta: { title: "Sign In", guest: true },
            beforeEnter: () => requireUnauth({ name: "welcome" }, router, pinia),
        },
        {
            path: "/welcome/",
            name: "welcome",
            component: () => import("@/views/ViewWelcome.vue"),
            meta: { title: "Welcome" },
            beforeEnter: () => requireInitialized(router, pinia),
        },
        ...makeCRUDRoutes({
            component: async () => (await import("@vueda/views/ViewActionRouter.vue")).default,
            authRedirect: { name: "sign-in" },
            groupsRedirect: { name: "welcome" },
            actionRedirect: { name: "not-found" },
            groups: [],
            vueApp: app,
            router,
            pinia,
        }),
        {
            path: "/:pathMatch(.*)*",
            name: "not-found",
            component: async () => (await import("@vueda/views/ViewNotFound.vue")).default,
            meta: {
                title: "Not Found",
                titles: {
                    view: "Not Found",
                },
            },
            beforeEnter: () => requireInitialized(router, pinia),
            props: (route) => {
                return {
                    ...(route.params || {}),
                    ...(route.query || {}),
                    title: route.meta.title,
                };
            },
        },
    ];

    for (const route of routes) {
        router.addRoute(route);
    }

    return router;
}
