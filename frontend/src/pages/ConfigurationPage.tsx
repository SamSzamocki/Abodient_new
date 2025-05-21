
import React from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Upload } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

const ConfigurationPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-foreground">Configuration</h1>
      <p className="text-muted-foreground mb-6">
        Manage system-wide settings and configurations here.
      </p>
      <Card>
        <CardHeader>
          <CardTitle>System Prompt</CardTitle>
          <CardDescription>
            Define the base behavior and instructions for the AI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid w-full gap-1.5">
            <Label htmlFor="system-prompt">Prompt</Label>
            <Textarea 
              placeholder="Enter your system prompt here..." 
              id="system-prompt" 
              rows={8} 
              className="min-h-[150px]"
            />
          </div>
        </CardContent>
        <CardFooter className="border-t px-6 py-4">
           <Button>Save Prompt</Button>
        </CardFooter>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Upload Configuration / Knowledge Files</CardTitle>
          <CardDescription>
            Upload relevant documents or configuration files.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-border rounded-lg min-h-[150px]">
            <Upload className="h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-muted-foreground mb-2">Drag & drop files here or</p>
            <Button variant="outline">
              <Upload className="mr-2 h-4 w-4" /> Select Files
            </Button>
            <p className="text-xs text-muted-foreground mt-3">
              Supported file types: .txt, .json, .csv (Max 5MB)
            </p>
          </div>
        </CardContent>
         <CardFooter className="border-t px-6 py-4">
           <Button disabled>Upload Files</Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ConfigurationPage;
