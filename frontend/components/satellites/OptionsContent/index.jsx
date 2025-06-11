// utils
import { memo } from "react";

// components and styles
import ObjectFiltering from "@/components/satellites/ObjectFiltering";
import styles from "@/styles/shared/CesiumOptions.module.scss";

const OptionsContent = ({
  toggleOptions,
  objectCategories,
  toggleCategoryVisibility,
}) => {
  return (
    <div className={styles["navigation"]}>
      <button
        onClick={toggleOptions}
        className={`${styles["nav-toggle"]} ${styles["nav-open"]}`}
      >
        Close options
      </button>
      <ObjectFiltering
        objectCategories={objectCategories}
        toggleCategoryVisibility={toggleCategoryVisibility}
      />
    </div>
  );
};

export default memo(OptionsContent);
