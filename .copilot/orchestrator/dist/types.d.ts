import { z } from 'zod';
export declare const SessionSchema: z.ZodObject<{
    session_id: z.ZodString;
    topic: z.ZodString;
    created: z.ZodString;
    last_active: z.ZodString;
    coordinator_model: z.ZodDefault<z.ZodEnum<["premium", "standard", "cheap"]>>;
}, "strip", z.ZodTypeAny, {
    session_id: string;
    topic: string;
    created: string;
    last_active: string;
    coordinator_model: "premium" | "standard" | "cheap";
}, {
    session_id: string;
    topic: string;
    created: string;
    last_active: string;
    coordinator_model?: "premium" | "standard" | "cheap" | undefined;
}>;
export type Session = z.infer<typeof SessionSchema>;
export interface TopicState {
    name: string;
    path: string;
    plan?: string;
    task?: string;
    session?: Session;
    delegations: DelegationInfo[];
}
export declare const DelegationStatusSchema: z.ZodEnum<["PENDING", "IN_PROGRESS", "COMPLETE", "BLOCKED"]>;
export declare const DelegationContextSchema: z.ZodObject<{
    files: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
    plan_excerpt: z.ZodOptional<z.ZodString>;
    constraints: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    files?: string[] | undefined;
    plan_excerpt?: string | undefined;
    constraints?: string | undefined;
}, {
    files?: string[] | undefined;
    plan_excerpt?: string | undefined;
    constraints?: string | undefined;
}>;
export type DelegationContext = z.infer<typeof DelegationContextSchema>;
export interface DelegationInfo {
    id: string;
    agent: string;
    task: string;
    context: DelegationContext;
    model_tier: 'premium' | 'standard' | 'cheap';
    status: z.infer<typeof DelegationStatusSchema>;
    created: string;
    result_path?: string;
}
export declare const CreateTopicArgsSchema: z.ZodObject<{
    name: z.ZodString;
    description: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    name: string;
    description?: string | undefined;
}, {
    name: string;
    description?: string | undefined;
}>;
export declare const SwitchTopicArgsSchema: z.ZodObject<{
    name: z.ZodString;
}, "strip", z.ZodTypeAny, {
    name: string;
}, {
    name: string;
}>;
export declare const DelegateToArgsSchema: z.ZodObject<{
    agent: z.ZodString;
    task: z.ZodString;
    context: z.ZodOptional<z.ZodObject<{
        files: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
        plan_excerpt: z.ZodOptional<z.ZodString>;
        constraints: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        files?: string[] | undefined;
        plan_excerpt?: string | undefined;
        constraints?: string | undefined;
    }, {
        files?: string[] | undefined;
        plan_excerpt?: string | undefined;
        constraints?: string | undefined;
    }>>;
    model_tier: z.ZodDefault<z.ZodEnum<["premium", "standard", "cheap"]>>;
    blocking: z.ZodDefault<z.ZodBoolean>;
}, "strip", z.ZodTypeAny, {
    agent: string;
    task: string;
    model_tier: "premium" | "standard" | "cheap";
    blocking: boolean;
    context?: {
        files?: string[] | undefined;
        plan_excerpt?: string | undefined;
        constraints?: string | undefined;
    } | undefined;
}, {
    agent: string;
    task: string;
    context?: {
        files?: string[] | undefined;
        plan_excerpt?: string | undefined;
        constraints?: string | undefined;
    } | undefined;
    model_tier?: "premium" | "standard" | "cheap" | undefined;
    blocking?: boolean | undefined;
}>;
export declare const CheckDelegationsArgsSchema: z.ZodObject<{
    topic: z.ZodOptional<z.ZodString>;
    agent: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    topic?: string | undefined;
    agent?: string | undefined;
}, {
    topic?: string | undefined;
    agent?: string | undefined;
}>;
export declare const MergeResultsArgsSchema: z.ZodObject<{
    delegation_id: z.ZodString;
}, "strip", z.ZodTypeAny, {
    delegation_id: string;
}, {
    delegation_id: string;
}>;
export declare const ArchiveTopicArgsSchema: z.ZodObject<{
    name: z.ZodString;
}, "strip", z.ZodTypeAny, {
    name: string;
}, {
    name: string;
}>;
export declare const ModelTiersSchema: z.ZodObject<{
    premium: z.ZodDefault<z.ZodString>;
    standard: z.ZodDefault<z.ZodString>;
    cheap: z.ZodDefault<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    premium: string;
    standard: string;
    cheap: string;
}, {
    premium?: string | undefined;
    standard?: string | undefined;
    cheap?: string | undefined;
}>;
export declare const ConfigSchema: z.ZodObject<{
    model_tiers: z.ZodOptional<z.ZodObject<{
        premium: z.ZodDefault<z.ZodString>;
        standard: z.ZodDefault<z.ZodString>;
        cheap: z.ZodDefault<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        premium: string;
        standard: string;
        cheap: string;
    }, {
        premium?: string | undefined;
        standard?: string | undefined;
        cheap?: string | undefined;
    }>>;
    defaults: z.ZodOptional<z.ZodObject<{
        coordinator: z.ZodDefault<z.ZodEnum<["premium", "standard", "cheap"]>>;
        specialist: z.ZodDefault<z.ZodEnum<["premium", "standard", "cheap"]>>;
    }, "strip", z.ZodTypeAny, {
        coordinator: "premium" | "standard" | "cheap";
        specialist: "premium" | "standard" | "cheap";
    }, {
        coordinator?: "premium" | "standard" | "cheap" | undefined;
        specialist?: "premium" | "standard" | "cheap" | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    model_tiers?: {
        premium: string;
        standard: string;
        cheap: string;
    } | undefined;
    defaults?: {
        coordinator: "premium" | "standard" | "cheap";
        specialist: "premium" | "standard" | "cheap";
    } | undefined;
}, {
    model_tiers?: {
        premium?: string | undefined;
        standard?: string | undefined;
        cheap?: string | undefined;
    } | undefined;
    defaults?: {
        coordinator?: "premium" | "standard" | "cheap" | undefined;
        specialist?: "premium" | "standard" | "cheap" | undefined;
    } | undefined;
}>;
export type Config = z.infer<typeof ConfigSchema>;
