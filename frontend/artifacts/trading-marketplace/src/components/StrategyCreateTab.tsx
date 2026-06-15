import { useState, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useCreateStrategy, getListStrategiesQueryKey } from "@/lib/api-client/api";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { UploadCloud, CheckCircle } from "lucide-react";

const formSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  minInvest: z.coerce.number().min(1, "Minimum investment must be greater than 0"),
  withdrawalPolicy: z.string().optional(),
  availability: z.string().default("all"),
  userName: z.string().optional(),
  userAccount: z.string().optional(),
  tradesHistoryFrom: z.string().optional(),
  description: z.string().optional(),
  passwordProtected: z.boolean().default(false),
  // Performance fee
  performanceFeeEnabled: z.boolean().default(true),
  performanceFee: z.coerce.number().min(0).max(100),
  performanceAgentFee: z.coerce.number().min(0).max(100),
  // Entry fee
  entryFeeEnabled: z.boolean().default(false),
  entryFee: z.coerce.number().min(0).max(100),
  entryAgentFee: z.coerce.number().min(0).max(100),
  // Subscription fee
  subscriptionFeeEnabled: z.boolean().default(false),
  subscriptionFeeType: z.string().default("monthly"),
  subscriptionFee: z.coerce.number().min(0),
  subscriptionAgentFee: z.coerce.number().min(0).max(100),
});

export default function StrategyCreateTab() {
  const [isCreating, setIsCreating] = useState(false);
  const [logoSrc, setLogoSrc] = useState<string | null>(null);
  const logoRef = useRef<HTMLInputElement>(null);
  const createStrategy = useCreateStrategy();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      minInvest: 100,
      withdrawalPolicy: "anytime",
      availability: "all",
      userName: "",
      userAccount: "",
      tradesHistoryFrom: "",
      description: "",
      passwordProtected: false,
      performanceFeeEnabled: true,
      performanceFee: 30,
      performanceAgentFee: 0,
      entryFeeEnabled: false,
      entryFee: 0,
      entryAgentFee: 0,
      subscriptionFeeEnabled: false,
      subscriptionFeeType: "monthly",
      subscriptionFee: 0,
      subscriptionAgentFee: 0,
    },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    createStrategy.mutate(
      {
        data: {
          name: values.name,
          minInvest: values.minInvest,
          withdrawalPolicy: values.withdrawalPolicy || "anytime",
          passwordProtected: values.passwordProtected,
          availability: values.availability,
          userName: values.availability === "userName" ? values.userName : null,
          userAccount: values.availability === "userName" ? values.userAccount : null,
          tradesHistoryFrom: values.tradesHistoryFrom || null,
          description: values.description || null,
          performanceFeeEnabled: values.performanceFeeEnabled,
          performanceFee: values.performanceFeeEnabled ? values.performanceFee : 0,
          performanceAgentFee: values.performanceFeeEnabled ? values.performanceAgentFee : 0,
          entryFeeEnabled: values.entryFeeEnabled,
          entryFee: values.entryFeeEnabled ? values.entryFee : 0,
          entryAgentFee: values.entryFeeEnabled ? values.entryAgentFee : 0,
          subscriptionFeeEnabled: values.subscriptionFeeEnabled,
          subscriptionFeeType: values.subscriptionFeeEnabled ? values.subscriptionFeeType : "monthly",
          subscriptionFee: values.subscriptionFeeEnabled ? values.subscriptionFee : 0,
          subscriptionAgentFee: values.subscriptionFeeEnabled ? values.subscriptionAgentFee : 0,
        },
      },
      {
        onSuccess: () => {
          toast({ title: "Strategy Created", description: "Your strategy has been successfully created." });
          queryClient.invalidateQueries({ queryKey: getListStrategiesQueryKey() });
          setIsCreating(false);
          form.reset();
          setLogoSrc(null);
        },
        onError: () => {
          toast({ title: "Error", description: "Failed to create strategy.", variant: "destructive" });
        },
      }
    );
  };

  if (!isCreating) {
    return (
      <div className="py-16 flex flex-col items-center justify-center border border-dashed rounded-lg bg-gray-50/30">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M21 13V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3H11M21 5L12 14M21 5H16M21 5V10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h3 className="text-lg font-medium mb-1">There are no active strategies</h3>
        <p className="text-muted-foreground mb-6">Create your first strategy to start accepting investments</p>
        <Button onClick={() => setIsCreating(true)} variant="outline">Create Strategy</Button>
      </div>
    );
  }

  const formValues = form.watch();

  return (
    <div className="max-w-3xl">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">Create Strategy</h2>
        <p className="text-muted-foreground text-sm">Set up your strategy parameters to attract investors.</p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          {/* Logo */}
          <div className="flex items-center gap-6 mb-8">
            <div
              onClick={() => logoRef.current?.click()}
              className="w-24 h-24 rounded-full border-2 border-dashed flex flex-col items-center justify-center text-muted-foreground bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors overflow-hidden"
            >
              {logoSrc ? (
                <img src={logoSrc} alt="logo" className="w-full h-full object-cover" />
              ) : (
                <>
                  <UploadCloud className="w-6 h-6 mb-1" />
                  <span className="text-[10px]">Upload Logo</span>
                </>
              )}
            </div>
            <input ref={logoRef} type="file" accept="image/*" className="hidden" onChange={e => {
              const f = e.target.files?.[0];
              if (f) { const r = new FileReader(); r.onload = () => setLogoSrc(r.result as string); r.readAsDataURL(f); }
            }} />
            <div>
              <h3 className="text-sm font-medium mb-1">Strategy Logo</h3>
              <p className="text-xs text-muted-foreground">Recommended size: 256x256px. JPG, PNG or SVG.</p>
            </div>
          </div>

          {/* Main fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FormField control={form.control} name="name" render={({ field }) => (
              <FormItem><FormLabel>Strategy Name</FormLabel><FormControl><Input placeholder="Strategy Name" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="withdrawalPolicy" render={({ field }) => (
              <FormItem>
                <FormLabel>Withdrawal Policy</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl><SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger></FormControl>
                  <SelectContent>
                    <SelectItem value="anytime">Anytime</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )} />
            <FormField control={form.control} name="minInvest" render={({ field }) => (
              <FormItem><FormLabel>Min Investment, USD</FormLabel><FormControl><Input type="number" placeholder="Min Investment" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <FormField control={form.control} name="tradesHistoryFrom" render={({ field }) => (
              <FormItem><FormLabel>Trades History From</FormLabel><FormControl><Input type="datetime-local" placeholder="From" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
          </div>

          {/* Availability */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="text-sm font-medium">Strategy Availability</div>
            <FormField control={form.control} name="availability" render={({ field }) => (
              <FormItem>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="userGroup">User Group</SelectItem>
                    <SelectItem value="userName">User Name + Account</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )} />
            {formValues.availability === "userName" && (
              <div className="grid grid-cols-2 gap-3">
                <FormField control={form.control} name="userName" render={({ field }) => (
                  <FormItem><FormLabel className="text-xs">User Name</FormLabel><FormControl><Input placeholder="User name" {...field} /></FormControl><FormMessage /></FormItem>
                )} />
                <FormField control={form.control} name="userAccount" render={({ field }) => (
                  <FormItem><FormLabel className="text-xs">Account</FormLabel><FormControl><Input placeholder="Account" {...field} /></FormControl><FormMessage /></FormItem>
                )} />
              </div>
            )}
          </div>

          {/* Description */}
          <FormField control={form.control} name="description" render={({ field }) => (
            <FormItem><FormLabel>Strategy Description</FormLabel><FormControl><Textarea placeholder="Strategy Description" className="h-32 resize-none" {...field} /></FormControl><FormMessage /></FormItem>
          )} />

          {/* Password Protected */}
          <FormField control={form.control} name="passwordProtected" render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div><FormLabel className="text-sm font-medium">Password protected</FormLabel><p className="text-xs text-muted-foreground">Require password to connect</p></div>
              <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
            </FormItem>
          )} />

          <div className="border-t pt-2" />

          {/* Performance Fee */}
          <div className="border rounded-lg p-4 space-y-3">
            <FormField control={form.control} name="performanceFeeEnabled" render={({ field }) => (
              <FormItem className="flex flex-row items-center justify-between">
                <FormLabel className="text-sm font-medium">Performance Fee</FormLabel>
                <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
              </FormItem>
            )} />
            {formValues.performanceFeeEnabled && (
              <div className="grid grid-cols-2 gap-4">
                <FormField control={form.control} name="performanceFee" render={({ field }) => (
                  <FormItem><FormLabel className="text-xs">Fee (%)</FormLabel><FormControl><Input type="number" placeholder="Fee %" {...field} /></FormControl><FormMessage /></FormItem>
                )} />
                <FormField control={form.control} name="performanceAgentFee" render={({ field }) => (
                  <FormItem><FormLabel className="text-xs">Agent Fee (%)</FormLabel><FormControl><Input type="number" placeholder="Agent %" {...field} /></FormControl><FormMessage /></FormItem>
                )} />
              </div>
            )}
          </div>

          {/* Subscription Fee */}
          <div className="border rounded-lg p-4 space-y-3">
            <FormField control={form.control} name="subscriptionFeeEnabled" render={({ field }) => (
              <FormItem className="flex flex-row items-center justify-between">
                <FormLabel className="text-sm font-medium">Subscription Fee</FormLabel>
                <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
              </FormItem>
            )} />
            {formValues.subscriptionFeeEnabled && (
              <>
                <FormField control={form.control} name="subscriptionFeeType" render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs">Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="annual">Annual</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormItem>
                )} />
                <div className="grid grid-cols-2 gap-4">
                  <FormField control={form.control} name="subscriptionFee" render={({ field }) => (
                    <FormItem><FormLabel className="text-xs">Fee (USD)</FormLabel><FormControl><Input type="number" placeholder="Fee" {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                  <FormField control={form.control} name="subscriptionAgentFee" render={({ field }) => (
                    <FormItem><FormLabel className="text-xs">Agent Fee (%)</FormLabel><FormControl><Input type="number" placeholder="Agent %" {...field} /></FormControl><FormMessage /></FormItem>
                  )} />
                </div>
              </>
            )}
          </div>

          {/* Entry Fee */}
          <div className="border rounded-lg p-4 space-y-3">
            <FormField control={form.control} name="entryFeeEnabled" render={({ field }) => (
              <FormItem className="flex flex-row items-center justify-between">
                <FormLabel className="text-sm font-medium">Entry Fee</FormLabel>
                <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
              </FormItem>
            )} />
            {formValues.entryFeeEnabled && (
              <div className="grid grid-cols-2 gap-4">
                <FormField control={form.control} name="entryFee" render={({ field }) => (
                  <FormItem><FormLabel className="text-xs">Fee (%)</FormLabel><FormControl><Input type="number" placeholder="Fee %" {...field} /></FormControl><FormMessage /></FormItem>
                )} />
                <FormField control={form.control} name="entryAgentFee" render={({ field }) => (
                  <FormItem><FormLabel className="text-xs">Agent Fee (%)</FormLabel><FormControl><Input type="number" placeholder="Agent %" {...field} /></FormControl><FormMessage /></FormItem>
                )} />
              </div>
            )}
          </div>

          <div className="border-t pt-2" />
          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
            <Button type="submit" disabled={createStrategy.isPending} className="bg-[#111111] hover:bg-black/90">
              {createStrategy.isPending ? "Creating..." : "Create Strategy"}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
