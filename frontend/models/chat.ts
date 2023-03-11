import { Model } from "@/models/base";
import { ulid } from "ulid";

enum Role {
  USER = "user",
  ASSISTANT = "assistant",
}

class Chat extends Model {
  /**
   * The Role enum
   * @enum @static
   */
  public static readonly Role = Role;

  /**
   * The chat's text message
   * @readonly
   */
  public readonly message: string;

  /**
   * The unique identifier of the chat's author
   * @readonly
   */
  public readonly author: string;

  /**
   * The id of the chat
   * @readonly
   */
  public readonly id: string = ulid();

  /**
   * The timestamp that the chat was created at
   * @readonly
   */
  public readonly timestamp: number = Math.floor(Date.now() / 1000);

  /**
   * The role of the chat's author
   * @readonly
   */
  public readonly role: Role = Role.USER;

  constructor(
    message: string,
    author: string,
    id?: string,
    timestamp?: number,
    role?: Role
  ) {
    super();
    this.message = message;
    this.author = author;
    id && (this.id = id);
    timestamp && (this.timestamp = timestamp);
    role && (this.role = role);
  }

  /**
   * Creates a new Chat instance from a JSON object
   *
   * @static
   * @param json The JSON object to create the Chat instance from
   * @returns The Chat instance
   */
  public static fromJSON(
    json:
      | {
          message: string;
          author: string;
        }
      | {
          message: string;
          author: string;
          id: string;
          timestamp: number;
          role: Role;
        }
  ): Chat {
    if ("id" in json && "timestamp" in json && "role" in json)
      return new Chat(
        json.message,
        json.author,
        json.id,
        json.timestamp,
        json.role
      );
    else return new Chat(json.message, json.author);
  }

  public toJSON(): {
    message: string;
    author: string;
    id: string;
    timestamp: number;
    role: Role;
  } {
    return {
      message: this.message,
      author: this.author,
      id: this.id,
      timestamp: this.timestamp,
      role: this.role,
    };
  }
}

export default Chat;
