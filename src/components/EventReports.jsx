import React from "react";
import {
  Datagrid,
  DateField,
  DeleteButton,
  List,
  NumberField,
  Pagination,
  ReferenceField,
  Show,
  Tab,
  TabbedShowLayout,
  TextField,
  TopToolbar,
  useRecordContext,
  useTranslate,
} from "react-admin";
import PageviewIcon from "@mui/icons-material/Pageview";
import ReportIcon from "@mui/icons-material/Warning";
import ViewListIcon from "@mui/icons-material/ViewList";

const date_format = {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
};

const ReportPagination = () => (
  <Pagination rowsPerPageOptions={[10, 25, 50, 100, 500, 1000]} />
);

export const ReportShow = props => {
  const translate = useTranslate();
  return (
    <Show {...props} actions={<ReportShowActions />}>
      <TabbedShowLayout>
        <Tab
          label={translate("synapseadmin.reports.tabs.basic", {
            smart_count: 1,
          })}
          icon={<ViewListIcon />}
        >
          <DateField
            source="received_ts"
            showTime
            options={date_format}
            sortable={true}
          />
          <ReferenceField source="user_id" reference="users">
            <TextField source="id" />
          </ReferenceField>
          <NumberField source="score" />
          <TextField source="reason" />
          <TextField source="name" />
          <TextField
            source="canonical_alias"
            label="resources.rooms.fields.canonical_alias"
          />
          <ReferenceField
            source="room_id"
            reference="rooms"
            link="show"
            label="resources.rooms.fields.room_id"
          >
            <TextField source="id" />
          </ReferenceField>
        </Tab>

        <Tab
          label="synapseadmin.reports.tabs.detail"
          icon={<PageviewIcon />}
          path="detail"
        >
          <DateField
            source="event_json.origin_server_ts"
            showTime
            options={date_format}
            sortable={true}
          />
          <ReferenceField source="sender" reference="users">
            <TextField source="id" />
          </ReferenceField>
          <TextField source="sender" label="Sender (raw user ID)" />
          <TextField source="event_id" />
          <TextField source="event_json.origin" />
          <TextField source="event_json.type" />
          <TextField source="event_json.content.msgtype" />
          <TextField source="event_json.content.body" />
          <TextField source="event_json.content.format" />
          <TextField source="event_json.content.formatted_body" />
          <TextField source="event_json.content.algorithm" />
          <TextField
            source="event_json.content.device_id"
            label="resources.devices.fields.device_id"
          />
        </Tab>
      </TabbedShowLayout>
    </Show>
  );
};

const ReportShowActions = () => {
  const record = useRecordContext();

  return (
    <TopToolbar>
      <DeleteButton
        record={record}
        mutationMode="pessimistic"
        confirmTitle="resources.reports.action.erase.title"
        confirmContent="resources.reports.action.erase.content"
      />
    </TopToolbar>
  );
};

export const ReportList = props => (
  <List
    {...props}
    pagination={<ReportPagination />}
    sort={{ field: "received_ts", order: "DESC" }}
  >
    <Datagrid rowClick="show" bulkActionButtons={false}>
      <TextField source="id" sortable={false} />
      <DateField
        source="received_ts"
        showTime
        options={date_format}
        sortable={true}
      />
      <TextField sortable={false} source="user_id" />
      <TextField sortable={false} source="name" />
      <TextField sortable={false} source="score" />
    </Datagrid>
  </List>
);

const resource = {
  name: "reports",
  icon: ReportIcon,
  list: ReportList,
  show: ReportShow,
};

export default resource;
