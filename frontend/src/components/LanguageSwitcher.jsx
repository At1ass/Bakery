import React from 'react';
import { useTranslation } from 'react-i18next';
import './LanguageSwitcher.css';

const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const currentLanguage = i18n.language;

  return (
    <div className="language-switcher">
      <label className="language-label">{t('language.switch')}:</label>
      <div className="language-buttons">
        <button
          className={`language-btn ${currentLanguage === 'en' ? 'active' : ''}`}
          onClick={() => changeLanguage('en')}
          title={t('language.english')}
        >
          🇺🇸 EN
        </button>
        <button
          className={`language-btn ${currentLanguage === 'ru' ? 'active' : ''}`}
          onClick={() => changeLanguage('ru')}
          title={t('language.russian')}
        >
          🇷🇺 RU
        </button>
      </div>
    </div>
  );
};

export default LanguageSwitcher; 