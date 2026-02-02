export declare function createTopic(args: unknown): Promise<{
    content: {
        type: 'text';
        text: string;
    }[];
}>;
export declare function listTopicsTool(): Promise<{
    content: {
        type: 'text';
        text: string;
    }[];
}>;
export declare function switchTopic(args: unknown): Promise<{
    content: {
        type: 'text';
        text: string;
    }[];
}>;
export declare function delegateTo(args: unknown): Promise<{
    content: {
        type: 'text';
        text: string;
    }[];
}>;
export declare function checkDelegations(args: unknown): Promise<{
    content: {
        type: 'text';
        text: string;
    }[];
}>;
export declare const toolDefinitions: ({
    name: string;
    description: string;
    inputSchema: {};
} | {
    name: string;
    description: string;
    inputSchema: import("zod").ZodObject<{
        name: import("zod").ZodString;
    }, "strip", import("zod").ZodTypeAny, {
        name: string;
    }, {
        name: string;
    }>;
} | {
    name: string;
    description: string;
    inputSchema: import("zod").ZodObject<{
        agent: import("zod").ZodString;
        task: import("zod").ZodString;
        context: import("zod").ZodOptional<import("zod").ZodObject<{
            files: import("zod").ZodOptional<import("zod").ZodArray<import("zod").ZodString, "many">>;
            plan_excerpt: import("zod").ZodOptional<import("zod").ZodString>;
            constraints: import("zod").ZodOptional<import("zod").ZodString>;
        }, "strip", import("zod").ZodTypeAny, {
            files?: string[] | undefined;
            plan_excerpt?: string | undefined;
            constraints?: string | undefined;
        }, {
            files?: string[] | undefined;
            plan_excerpt?: string | undefined;
            constraints?: string | undefined;
        }>>;
        model_tier: import("zod").ZodDefault<import("zod").ZodEnum<["premium", "standard", "cheap"]>>;
        blocking: import("zod").ZodDefault<import("zod").ZodBoolean>;
    }, "strip", import("zod").ZodTypeAny, {
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
} | {
    name: string;
    description: string;
    inputSchema: import("zod").ZodObject<{
        topic: import("zod").ZodOptional<import("zod").ZodString>;
        agent: import("zod").ZodOptional<import("zod").ZodString>;
    }, "strip", import("zod").ZodTypeAny, {
        topic?: string | undefined;
        agent?: string | undefined;
    }, {
        topic?: string | undefined;
        agent?: string | undefined;
    }>;
})[];
