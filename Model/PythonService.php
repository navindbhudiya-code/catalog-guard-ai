<?php
/**
 * Thin HTTP client to the CatalogGuard Python service.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Model;

use Magento\Framework\App\Config\ScopeConfigInterface;
use Magento\Framework\HTTP\Client\Curl;
use Magento\Framework\Serialize\Serializer\Json;

class PythonService
{
    private const XML_PATH_BASE_URL = 'catalogguard/service/base_url';

    public function __construct(
        private readonly ScopeConfigInterface $scopeConfig,
        private readonly Curl $curl,
        private readonly Json $json
    ) {
    }

    public function getBaseUrl(): string
    {
        return rtrim((string) $this->scopeConfig->getValue(self::XML_PATH_BASE_URL), '/');
    }

    /**
     * Trigger an audit run on the Python service and return the decoded summary.
     *
     * @return array<string, mixed>
     */
    public function runAudit(string $checks = 'sanity,attributes,duplicates,seo'): array
    {
        $this->curl->addHeader('Content-Type', 'application/json');
        $this->curl->post(
            $this->getBaseUrl() . '/audit',
            $this->json->serialize(['checks' => $checks])
        );

        return $this->decode($this->curl->getBody());
    }

    /**
     * Fetch the latest audit report from the Python service.
     *
     * @return array<string, mixed>
     */
    public function getLatestReport(): array
    {
        $this->curl->get($this->getBaseUrl() . '/report/latest');

        return $this->decode($this->curl->getBody());
    }

    /**
     * @return array<string, mixed>
     */
    private function decode(string $body): array
    {
        if ($body === '') {
            return [];
        }

        $decoded = $this->json->unserialize($body);

        return is_array($decoded) ? $decoded : [];
    }
}
