
import { initChatModel } from "langchain/chat_models/universal";
import type { ContextLogger } from "../logging/logging.service";

// Model configuration
export interface GenGetConfig {
    modelName: string;
    modelProvider: string;
    apiKey: string;
    baseUrl?: string;
    temperature?: number;
    maxTokens?: number;
}

// Infer model type from LangChain
type ChatModel = Awaited<ReturnType<typeof initChatModel>>;

export class GenerationModel {
    private modelPromise?: Promise<ChatModel>;

    private constructor(
        private readonly config: GenGetConfig,
        private readonly logger: ContextLogger,
    ) {}

    // Create and initialize the service
    public static async init_class(
        config: GenGetConfig,
        logger: ContextLogger,
    ): Promise<GenerationModel> {
        const instance = new GenerationModel(config, logger);

        // Initialize once before returning
        await instance.getChatModel();

        return instance;
    }

    // Return the same initialized model
    public async getChatModel(): Promise<ChatModel> {
        if (!this.modelPromise) {
            this.modelPromise = this.createModel().catch((error) => {
                // Reset initialization so it can be retried
                this.modelPromise = undefined;
                throw error;
            });
        }

        return this.modelPromise;
    }

    // Initialize LangChain chat model
    private async createModel(): Promise<ChatModel> {
        try {
            this.logger.info(
                { model: this.config.modelName },
                "Initializing chat model",
            );

            const model = await initChatModel(
                this.config.modelName,
                {
                    modelProvider: this.config.modelProvider,
                    apiKey: this.config.apiKey,
                    temperature: this.config.temperature,
                    maxTokens: this.config.maxTokens,

                    ...(this.config.baseUrl && {
                        configuration: {
                            baseURL: this.config.baseUrl,
                        },
                    }),
                },
            );

            this.logger.info(
                { model: this.config.modelName },
                "Chat model initialized successfully",
            );

            return model;
        } catch (error) {
            this.logger.error(
                { err: error },
                "Failed to initialize chat model",
            );

            throw error;
        }
    }
}
