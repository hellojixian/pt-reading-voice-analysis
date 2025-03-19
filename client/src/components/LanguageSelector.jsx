import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * 语言选择器组件
 * 允许用户在可用语言间切换
 */
const LanguageSelector = () => {
  const { t, i18n } = useTranslation();

  // 可用的语言选项
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'zh', name: '中文' }
  ];

  // 处理语言切换
  const changeLanguage = (e) => {
    const langCode = e.target.value;
    i18n.changeLanguage(langCode);
    // 保存语言偏好到本地存储
    localStorage.setItem('i18nextLng', langCode);
  };

  return (
    <div className="language-selector">
      <label htmlFor="language-select">{t('app.language')}: </label>
      <select
        id="language-select"
        value={i18n.language}
        onChange={changeLanguage}
      >
        {languages.map(lang => (
          <option key={lang.code} value={lang.code}>
            {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default LanguageSelector;
