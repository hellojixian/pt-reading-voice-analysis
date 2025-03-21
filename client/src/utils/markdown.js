import React from 'react';

/**
 * Simple function to render basic Markdown text
 *
 * @param {string} text - The text with Markdown formatting
 * @returns {JSX.Element|null} - Rendered React elements
 */
export const renderMarkdown = (text) => {
  if (!text) return null;

  // Process bold text first (before paragraph splitting)
  const processBoldText = (content) => {
    // Replace **text** with <strong>text</strong> using regex
    return content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  // Apply bold formatting
  const textWithBoldFormatting = processBoldText(text);

  // Split by line breaks to handle paragraphs
  const paragraphs = textWithBoldFormatting.split('\n\n');

  return (
    <>
      {paragraphs.map((paragraph, i) => {
        // Skip empty paragraphs
        if (!paragraph.trim()) return null;

        // Handle headers
        if (paragraph.startsWith('# ')) {
          return <h1 key={i} dangerouslySetInnerHTML={{ __html: paragraph.substring(2) }} />;
        } else if (paragraph.startsWith('## ')) {
          return <h2 key={i} dangerouslySetInnerHTML={{ __html: paragraph.substring(3) }} />;
        } else if (paragraph.startsWith('### ')) {
          return <h3 key={i} dangerouslySetInnerHTML={{ __html: paragraph.substring(4) }} />;
        }

        // Handle lists (simple implementation)
        if (paragraph.includes('\n- ')) {
          const items = paragraph.split('\n- ');
          return (
            <ul key={i}>
              {items[0] && <p dangerouslySetInnerHTML={{ __html: items[0] }} />}
              {items.slice(1).map((item, j) => (
                <li key={j} dangerouslySetInnerHTML={{ __html: item }} />
              ))}
            </ul>
          );
        }

        // Handle numbered lists (simple implementation)
        if (/\n\d+\.\s/.test(paragraph)) {
          const items = paragraph.split(/\n\d+\.\s/);
          return (
            <ol key={i}>
              {items[0] && <p dangerouslySetInnerHTML={{ __html: items[0] }} />}
              {items.slice(1).map((item, j) => (
                <li key={j} dangerouslySetInnerHTML={{ __html: item }} />
              ))}
            </ol>
          );
        }

        // Regular paragraph with line breaks
        const lines = paragraph.split('\n');
        return (
          <p key={i}>
            {lines.map((line, j) => (
              <React.Fragment key={j}>
                <span dangerouslySetInnerHTML={{ __html: line }} />
                {j < lines.length - 1 && <br />}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </>
  );
};

export default renderMarkdown;
