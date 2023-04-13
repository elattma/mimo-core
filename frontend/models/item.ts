import { Model } from "@/models/base";

class Item extends Model {
  /**
   * The id of the item
   * @readonly
   */
  public readonly id: string;

  /**
   * The title of the item
   * @readonly
   */
  public readonly title: string;

  /**
   * A link to the item's source
   * @readonly
   */
  public readonly link: string;

  /**
   * The icon to display alongside this item
   * @readonly
   */
  public readonly icon: string;

  /**
   * The id of the integration this item originated from
   * @readonly
   */
  public readonly integration: string;

  constructor(
    id: string,
    title: string,
    link: string,
    icon: string,
    integration: string
  ) {
    super();
    this.id = id;
    this.title = title;
    this.link = link;
    this.icon = icon;
    this.integration = integration;
  }

  /**
   * Creates a new Item instance from a JSON object
   *
   * @static
   * @param json The JSON object to create the Item instance from
   * @returns The Item instance
   */
  public static fromJSON(json: {
    id: string;
    title: string;
    link: string;
    icon: string;
    integration: string;
  }): Item {
    return new Item(
      json.id,
      json.title,
      json.link,
      json.icon,
      json.integration
    );
  }
}

export default Item;
