import { Model } from "@/models/base";

class Integration extends Model {
  /**
   * The id of the integration
   * @readonly
   */
  public readonly id: string;

  /**
   * The name of the integration
   * @readonly
   */
  public readonly name: string;

  /**
   * A description of the integration
   * @readonly
   */
  public readonly description: string;

  /**
   * An SVG icon for the integration
   * @readonly
   */
  public readonly icon: string;

  /**
   * The URL to authenticate with the integration
   * @readonly
   */
  public readonly oauth2_link: string;

  /**
   * The authorization status of the integration
   */
  public authorized: boolean = false;

  constructor(
    id: string,
    name: string,
    description: string,
    icon: string,
    oauth2_link: string,
    authorized: boolean = false
  ) {
    super();
    this.id = id;
    this.name = name;
    this.description = description;
    this.icon = icon;
    this.oauth2_link = oauth2_link;
    this.authorized = authorized;
  }

  public static fromJSON(json: {
    id: string;
    name: string;
    description: string;
    icon: string;
    oauth2_link: string;
    authorized: boolean;
  }): Integration {
    return new Integration(
      json.id,
      json.name,
      json.description,
      json.icon,
      json.oauth2_link,
      json.authorized
    );
  }
}

export default Integration;
