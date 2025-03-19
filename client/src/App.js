import React from 'react';
import { useTranslation } from 'react-i18next';
import ChatInterface from './components/ChatInterface';
import LanguageSelector from './components/LanguageSelector';

/**
 * 应用程序主组件
 */
const App = () => {
  const { t } = useTranslation();

  return (
    <div className="app-container">
      <header className="header">
        <h1>{t('app.title')}</h1>
        <LanguageSelector />
      </header>

      <main>
        <ChatInterface />
      </main>

      <footer>
        <p>&copy; {new Date().getFullYear()} 语音对话助手</p>
      </footer>
    </div>
  );
};

export default App;
