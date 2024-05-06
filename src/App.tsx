import { merge } from "lodash";
import polyglotI18nProvider from "ra-i18n-polyglot";

import { Admin, CustomRoutes, Resource, resolveBrowserLocale } from "react-admin";
import { Route } from "react-router-dom";

import reports from "./components/EventReports";
import { ImportFeature } from "./components/ImportFeature";
import LoginPage from "./components/LoginPage";
import registrationToken from "./components/RegistrationTokens";
import roomDirectory from "./components/RoomDirectory";
import destinations from "./components/destinations";
import rooms from "./components/rooms";
import userMediaStats from "./components/statistics";
import users from "./components/users";
import germanMessages from "./i18n/de";
import englishMessages from "./i18n/en";
import frenchMessages from "./i18n/fr";
import italianMessages from "./i18n/it";
import chineseMessages from "./i18n/zh";
import authProvider from "./synapse/authProvider";
import dataProvider from "./synapse/dataProvider";

// TODO: Can we use lazy loading together with browser locale?
const messages = {
  de: germanMessages,
  en: englishMessages,
  fr: frenchMessages,
  it: italianMessages,
  zh: chineseMessages,
};
const i18nProvider = polyglotI18nProvider(
  locale => (messages[locale] ? merge({}, messages.en, messages[locale]) : messages.en),
  resolveBrowserLocale(),
  [
    { locale: "en", name: "English" },
    { locale: "de", name: "Deutsch" },
    { locale: "fr", name: "Français" },
    { locale: "it", name: "Italiano" },
    { locale: "fa", name: "Persian(فارسی)" },
    { locale: "zh", name: "简体中文" },
  ]
);

const App = () => (
  <Admin
    disableTelemetry
    requireAuth
    loginPage={LoginPage}
    authProvider={authProvider}
    dataProvider={dataProvider}
    i18nProvider={i18nProvider}
  >
    <CustomRoutes>
      <Route path="/import_users" element={<ImportFeature />} />
    </CustomRoutes>
    <Resource {...users} />
    <Resource {...rooms} />
    <Resource {...userMediaStats} />
    <Resource {...reports} />
    <Resource {...roomDirectory} />
    <Resource {...destinations} />
    <Resource {...registrationToken} />
    <Resource name="connections" />
    <Resource name="devices" />
    <Resource name="room_members" />
    <Resource name="users_media" />
    <Resource name="joined_rooms" />
    <Resource name="pushers" />
    <Resource name="servernotices" />
    <Resource name="forward_extremities" />
    <Resource name="room_state" />
    <Resource name="destination_rooms" />
  </Admin>
);

export default App;
