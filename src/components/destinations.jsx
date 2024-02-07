import React from "react";
import {
  Button,
  Datagrid,
  DateField,
  List,
  Pagination,
  ReferenceField,
  ReferenceManyField,
  SearchInput,
  Show,
  Tab,
  TabbedShowLayout,
  TextField,
  TopToolbar,
  useRecordContext,
  useDelete,
  useNotify,
  useRefresh,
  useTranslate,
} from "react-admin";
import AutorenewIcon from "@mui/icons-material/Autorenew";
import DestinationsIcon from "@mui/icons-material/CloudQueue";
import FolderSharedIcon from "@mui/icons-material/FolderShared";
import ViewListIcon from "@mui/icons-material/ViewList";

const DestinationPagination = () => (
  <Pagination rowsPerPageOptions={[10, 25, 50, 100, 500, 1000]} />
);

const date_format = {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
};

const destinationRowSx = (record, _index) => ({
  backgroundColor: record.retry_last_ts > 0 ? "#ffcccc" : "white",
});

const destinationFilters = [<SearchInput source="destination" alwaysOn />];

export const DestinationReconnectButton = () => {
  const record = useRecordContext();
  const refresh = useRefresh();
  const notify = useNotify();
  const [handleReconnect, { isLoading }] = useDelete();

  // Reconnect is not required if no error has occurred. (`failure_ts`)
  if (!record || !record.failure_ts) return null;

  const handleClick = e => {
    // Prevents redirection to the detail page when clicking in the list
    e.stopPropagation();

    handleReconnect(
      "destinations",
      { id: record.id },
      {
        onSuccess: () => {
          notify("ra.notification.updated", {
            messageArgs: { smart_count: 1 },
          });
          refresh();
        },
        onError: () => {
          notify("ra.message.error", { type: "error" });
        },
      }
    );
  };

  return (
    <Button
      label="resources.destinations.action.reconnect"
      onClick={handleClick}
      disabled={isLoading}
    >
      <AutorenewIcon />
    </Button>
  );
};

const DestinationShowActions = () => (
  <TopToolbar>
    <DestinationReconnectButton />
  </TopToolbar>
);

const DestinationTitle = () => {
  const record = useRecordContext();
  const translate = useTranslate();
  return (
    <span>
      {translate("resources.destinations.name", 1)} {record.destination}
    </span>
  );
};

export const DestinationList = props => {
  return (
    <List
      {...props}
      filters={destinationFilters}
      pagination={<DestinationPagination />}
      sort={{ field: "destination", order: "ASC" }}
    >
      <Datagrid
        rowSx={destinationRowSx}
        rowClick={(id, _resource, _record) => `${id}/show/rooms`}
        bulkActionButtons={false}
      >
        <TextField source="destination" />
        <DateField source="failure_ts" showTime options={date_format} />
        <DateField source="retry_last_ts" showTime options={date_format} />
        <TextField source="retry_interval" />
        <TextField source="last_successful_stream_ordering" />
        <DestinationReconnectButton />
      </Datagrid>
    </List>
  );
};

export const DestinationShow = props => {
  const translate = useTranslate();
  return (
    <Show
      actions={<DestinationShowActions />}
      title={<DestinationTitle />}
      {...props}
    >
      <TabbedShowLayout>
        <Tab label="status" icon={<ViewListIcon />}>
          <TextField source="destination" />
          <DateField source="failure_ts" showTime options={date_format} />
          <DateField source="retry_last_ts" showTime options={date_format} />
          <TextField source="retry_interval" />
          <TextField source="last_successful_stream_ordering" />
        </Tab>

        <Tab
          label={translate("resources.rooms.name", { smart_count: 2 })}
          icon={<FolderSharedIcon />}
          path="rooms"
        >
          <ReferenceManyField
            reference="destination_rooms"
            target="destination"
            addLabel={false}
            pagination={<DestinationPagination />}
            perPage={50}
          >
            <Datagrid
              style={{ width: "100%" }}
              rowClick={(id, resource, record) => `/rooms/${id}/show`}
            >
              <TextField
                source="room_id"
                label="resources.rooms.fields.room_id"
              />
              <TextField source="stream_ordering" sortable={false} />
              <ReferenceField
                label="resources.rooms.fields.name"
                source="id"
                reference="rooms"
                sortable={false}
                link=""
              >
                <TextField source="name" sortable={false} />
              </ReferenceField>
            </Datagrid>
          </ReferenceManyField>
        </Tab>
      </TabbedShowLayout>
    </Show>
  );
};

const resource = {
  name: "destinations",
  icon: DestinationsIcon,
  list: DestinationList,
  show: DestinationShow,
};

export default resource;
