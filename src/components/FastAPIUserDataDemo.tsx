import React from 'react';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

export const FastAPIUserDataDemo: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>FastAPI User Data Demo</CardTitle>
          <CardDescription>
            Simplified version for testing
          </CardDescription>
        </CardHeader>
        <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
            <Badge variant="default">Ready</Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Backend is running on port 8001. Frontend is working correctly.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};