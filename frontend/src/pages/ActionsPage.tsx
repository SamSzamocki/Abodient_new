
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge"; // Assuming Badge component exists for status

// Sample data - replace with actual data from Supabase later
const actionsData = [
  { id: '1', type: 'Email Sent', person: 'John Doe', dateTime: '2025-05-20 10:00 AM', status: 'Completed' },
  { id: '2', type: 'Call Scheduled', person: 'Jane Smith', dateTime: '2025-05-21 02:30 PM', status: 'Pending' },
  { id: '3', type: 'Meeting Notes', person: 'Alex Johnson', dateTime: '2025-05-19 04:00 PM', status: 'Archived' },
  { id: '4', type: 'Task Created', person: 'System', dateTime: '2025-05-20 11:15 AM', status: 'In Progress' },
];

const ActionsPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-foreground">Actions</h1>
      <p className="text-muted-foreground mb-6">
        This page will list actions and their statuses. Connect to Supabase to manage real data.
      </p>
      <div className="bg-card border border-border rounded-lg shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Action Type</TableHead>
              <TableHead>Person Contacted</TableHead>
              <TableHead>Time/Date Details</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {actionsData.map((action) => (
              <TableRow key={action.id}>
                <TableCell>{action.type}</TableCell>
                <TableCell>{action.person}</TableCell>
                <TableCell>{action.dateTime}</TableCell>
                <TableCell>
                  <Badge variant={
                    action.status === 'Completed' ? 'default' : 
                    action.status === 'Pending' ? 'secondary' : 
                    action.status === 'In Progress' ? 'outline' : // Example, adjust as needed
                    'destructive' // For Archived or other statuses
                  }>
                    {action.status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
            {actionsData.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No actions to display.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default ActionsPage;
