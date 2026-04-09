import {registry} from "@web/core/registry";
import {browser} from "@web/core/browser/browser";

function requestPermission() {
    if (browser.Notification && browser.Notification.permission !== "granted") {
        browser.Notification.requestPermission();
    }
}

function showDesktopNotification(title, message) {
    if (browser.Notification && browser.Notification.permission === "granted") {
        new browser.Notification(title, {
            body: message,
            icon: "/web/static/img/favicon.ico",
        });
    }
}

const DesktopNotificationService = {
    dependencies: ["bus_service"],

    start(env, {bus_service}) {

        requestPermission();

        bus_service.addEventListener("notification", ({detail: notifications}) => {

            for (const {type, payload} of notifications) {

                if (type === "activity_notification") {

                    showDesktopNotification(
                        payload.title,
                        payload.message
                    );

                }

            }

        });

    },
};

registry.category("services").add("desktop_notification_service", DesktopNotificationService);