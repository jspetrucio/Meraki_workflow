import { useEffect, useState } from 'react';
import { CheckCircle, Loader2, Trash2 } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api } from '@/lib/api';
import type { MerakiProfile } from '@/lib/types';

interface ProfileListResponse {
  profiles: string[];
  active: string;
}

export function ProfilesTab() {
  const [profiles, setProfiles] = useState<string[]>([]);
  const [activeProfile, setActiveProfile] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<string | null>(null);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const data = await api.get<ProfileListResponse>('/api/v1/profiles');
      setProfiles(data.profiles);
      setActiveProfile(data.active);
    } catch (err) {
      console.error('Failed to load profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleActivateProfile = async (name: string) => {
    setActivating(name);
    try {
      await api.post<MerakiProfile>(`/api/v1/profiles/${name}/activate`, {});
      setActiveProfile(name);
    } catch (err) {
      console.error('Failed to activate profile:', err);
    } finally {
      setActivating(null);
    }
  };

  const handleDeleteProfile = async (name: string) => {
    // TODO: Implement delete endpoint in backend
    console.log('Delete profile:', name);
    setDeleteDialog(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4 py-4">
      <Card>
        <CardHeader>
          <CardTitle>Meraki Profiles</CardTitle>
          <CardDescription>
            Manage your Meraki Dashboard API profiles and credentials
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {profiles.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No profiles configured</p>
              <p className="text-sm mt-2">
                Configure profiles in ~/.meraki/credentials
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {profiles.map((profile) => (
                <Card key={profile} className="relative">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Label className="text-base font-medium">{profile}</Label>
                          {profile === activeProfile && (
                            <Badge variant="default" className="text-xs">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Active
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Meraki Dashboard Profile
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {profile !== activeProfile && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleActivateProfile(profile)}
                            disabled={activating === profile}
                          >
                            {activating === profile ? (
                              <>
                                <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                                Activating...
                              </>
                            ) : (
                              'Activate'
                            )}
                          </Button>
                        )}
                        {profile !== 'default' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteDialog(profile)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          <div className="pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              To add new profiles, edit <code className="bg-muted px-1 py-0.5 rounded">~/.meraki/credentials</code>
            </p>
          </div>
        </CardContent>
      </Card>

      <Dialog open={deleteDialog !== null} onOpenChange={() => setDeleteDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Profile</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the profile "{deleteDialog}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialog(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteDialog && handleDeleteProfile(deleteDialog)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
